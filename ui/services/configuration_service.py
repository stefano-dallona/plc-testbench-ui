from werkzeug.utils import secure_filename

import logging
import os
import uuid as Uuid
from operator import itemgetter
from itertools import groupby

from plctestbench.worker import *
from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.path_manager import *
from plctestbench.node import *
from plctestbench.settings import *


class ConfigurationService:
    
    _logger = logging.getLogger(__name__)
    
    def __init__(self, root_folder):
        self.root_folder = root_folder
    
    @staticmethod
    def itersubclasses(cls, _seen=None):
        """
        itersubclasses(cls)

        Generator over all subclasses of a given class, in depth first order.

        >>> list(itersubclasses(int)) == [bool]
        True
        >>> class A(object): pass
        >>> class B(A): pass
        >>> class C(A): pass
        >>> class D(B,C): pass
        >>> class E(D): pass
        >>> 
        >>> for cls in itersubclasses(A):
        ...     print(cls.__name__)
        B
        D
        E
        C
        >>> # get ALL (new-style) classes currently defined
        >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
        ['type', ...'tuple', ...]
        """
        
        if not isinstance(cls, type):
            raise TypeError('itersubclasses must be called with '
                            'new-style classes, not %.100r' % cls)
        if _seen is None: _seen = set()
        try:
            subs = cls.__subclasses__()
        except TypeError: # fails only when cls is type
            subs = cls.__subclasses__(cls)
        for sub in subs:
            if sub not in _seen:
                _seen.add(sub)
                yield sub
                for sub in ConfigurationService.itersubclasses(sub, _seen):
                    yield sub
    @staticmethod
    def hasSettings(cls):
        settings_class_name = cls.__name__ + "Settings"
        return settings_class_name in globals().keys()
    
    @staticmethod
    def find_loss_simulators():
        ConfigurationService._logger.info("Retrieving loss simulators ...")
        result = [cls.__name__ for cls in PacketLossSimulator.__subclasses__()]
        return result
    '''
    @staticmethod
    def find_loss_models():
        ConfigurationService._logger.info("Retrieving loss models ...")
        result = [cls.__name__ for cls in LossModel.__subclasses__()]
        return result
    '''
    @staticmethod
    def find_ecc_algorithms():
        ConfigurationService._logger.info("Retrieving ecc algorithms ...")
        result = [cls.__name__ for cls in PLCAlgorithm.__subclasses__()]
        return result
    
    @staticmethod
    def get_output_analyser_category(analyser_type: type) -> bool:
        if analyser_type.run == None:
            return False
        
        return_type_hint = analyser_type.run.__annotations__["return"] \
            if 'return' in analyser_type.run.__annotations__.keys() \
            else None
        
        # Return type of run method is iterable => the analyser is linear
        return "linear" if return_type_hint == None or hasattr(return_type_hint, "__iter__") else "scalar"
    
    @staticmethod
    def find_output_analysers(category: str = None):
        ConfigurationService._logger.info("Retrieving output analysers ...")
        result = [cls.__name__ for cls in ConfigurationService.itersubclasses(OutputAnalyser)
                  if ConfigurationService.hasSettings(cls) and (category == None or
                    category == ConfigurationService.get_output_analyser_category(cls))]
        return result
    
    @staticmethod
    def get_worker_class(settings_class):
        worker_name = settings_class.__name__.replace("Settings", "")
        ConfigurationService._logger.info(f"worker_name:{worker_name}")
        worker_constructor = globals()[worker_name] if worker_name in globals() else None
        ConfigurationService._logger.info(f"worker_constructor:{worker_constructor}")
        worker_constructor = worker_constructor if worker_constructor != None else settings_class
        return worker_constructor
    
    @staticmethod
    def get_worker_base_class(worker_class) -> Worker:
        ancestors = worker_class.__mro__
        for ancestor in [ancestor for ancestor in ancestors
                            if ancestor in [PacketLossSimulator, PLCAlgorithm, OutputAnalyser]]:
            return ancestor
        return None
    
    @staticmethod
    def find_settings_metadata():
        cs = ConfigurationService
        ConfigurationService._logger.info("Retrieving settings metadata ...")
        settingsInstances = [(cls(), cs.get_worker_class(cls), cs.get_worker_base_class(cs.get_worker_class(cls))) for cls in Settings.__subclasses__() \
                             if cs.get_worker_base_class(cs.get_worker_class(cls))]
        metadata = [
            {
                "property": category.__name__,
                "value": [
                {
                    "uuid": Uuid.uuid4(),
                    "name" : settings[1].__name__,
                    "settings" : [
                        {
                           "property": property,
                           "value": value,
                           "type": type(value).__name__,
                           "mandatory": True
                        }
                        for property, value in settings[0].settings.items() if not property.startswith("__")
                    ]
                } for settings in list(settingsMetadata) ]
            } for category, settingsMetadata in groupby(settingsInstances, key=itemgetter(2))
        ]
        return metadata
    
    def find_input_files(self):
        self._logger.info("Retrieving input files ...")
        path_manager = PathManager(self.root_folder)
        result = [ os.path.basename(original_track) for original_track in path_manager.get_original_tracks()]
        return result
    
    def upload_audio_files(self, file, total_file_size: int, total_chunks: int, current_chunk: int, offset: int):
        self._logger.info("Uploading file ...")
        save_path = os.path.join(self.root_folder, secure_filename(file.filename))
        
        # If the file already exists it's ok if we are appending to it,
        # but not if it's new file that would overwrite the existing one
        if os.path.exists(save_path) and current_chunk == 0:
            # 400 and 500s will tell dropzone that an error occurred and show an error
            raise UploadException('File already exists')
        
        try:
            with open(save_path, 'ab') as f:
                f.seek(int(offset))
                f.write(file.stream.read())
        except OSError:
            # log.exception will include the traceback so we can see what's wrong 
            self._logger.exception('Could not write to file')
            raise UploadException("Not sure why, but we couldn't write the file to disk")

        if current_chunk + 1 == total_chunks:
            # This was the last chunk, the file should be complete and the size we expect
            if os.path.getsize(save_path) != int(total_file_size):
                self._logger.error(f"File {file.filename} was completed, "
                        f"but has a size mismatch."
                        f"Was {os.path.getsize(save_path)} but we"
                        f" expected {total_file_size} ")
                raise UploadException('Size mismatch')
            else:
                self._logger.info(f'File {file.filename} has been uploaded successfully')
        else:
            self._logger.debug(f'Chunk {current_chunk + 1} of {total_chunks} '
                    f'for file {file.filename} complete')
    
class UploadException(Exception):
    
    def __init__(self, message):
        super().__init__(message)