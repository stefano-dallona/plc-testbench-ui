from werkzeug.utils import secure_filename

import logging
import os

from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.path_manager import *
from plctestbench.node import *

class ConfigurationService:
    
    _logger = logging.getLogger(__name__)
    
    def __init__(self, root_folder):
        self.root_folder = root_folder
    
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
    def find_output_analysers():
        ConfigurationService._logger.info("Retrieving output analysers ...")
        result = [cls.__name__ for cls in OutputAnalyser.__subclasses__()]
        return result
    
    @staticmethod
    def find_settings_metadata():
        ConfigurationService._logger.info("Retrieving settings metadata ...")
        settings = Settings()
        result = [{ "name": name, "type": type(getattr(settings, name)).__name__, "value" : getattr(settings, name) } for name in vars(settings) if not name.startswith("_")]
        return result
    
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