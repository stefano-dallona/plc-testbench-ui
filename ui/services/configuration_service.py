from werkzeug.utils import secure_filename

import logging
import os
import uuid as Uuid
from operator import itemgetter
from itertools import groupby
from collections import ChainMap, OrderedDict
from enum import Enum

from plctestbench.worker import *
from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.path_manager import *
from plctestbench.node import *
from plctestbench.settings import *

from ..models.filter import *
from ..repositories.mongodb.filter_repository import *


class ConfigurationService:

    _logger = logging.getLogger(__name__)

    def __init__(self, root_folder: str, filter_repository: FilterRepository):
        self.root_folder = root_folder
        self.filter_repository = filter_repository

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
        if _seen is None:
            _seen = set()
        try:
            subs = cls.__subclasses__()
        except TypeError:  # fails only when cls is type
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
        worker_constructor = globals(
        )[worker_name] if worker_name in globals() else None
        ConfigurationService._logger.info(
            f"worker_constructor:{worker_constructor}")
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
        settingsInstances = [(cls(), cs.get_worker_class(cls), cs.get_worker_base_class(cs.get_worker_class(cls))) for cls in Settings.__subclasses__()
                             if cs.get_worker_base_class(cs.get_worker_class(cls))]

        def get_setting_metadata(property, value):
            if isinstance(value, Enum):
                return {
                    "property": property,
                    "value": value.value,
                    "type": "select",
                    "options": [
                        member.value for member in type(value)],
                    "mandatory": True
                }
            else:
                return {
                    "property": property,
                    "value": value,
                    "type": type(value).__name__,
                    "mandatory": True
                }

        metadata = [
            {
                "property": category.__name__,
                "value": [
                    {
                        "uuid": Uuid.uuid4(),
                        "name": settings[1].__name__,
                        "settings": [
                            get_setting_metadata(property, value)
                            for property, value in settings[0].settings.items() if not property.startswith("__")
                        ],
                        "doc": settings[1].__doc__
                    } for settings in list(settingsMetadata)]
            } for category, settingsMetadata in groupby(settingsInstances, key=itemgetter(2))
        ]
        return metadata

    def get_search_fields(self):

        def get_field(setting):
            field = {
                setting["property"]: {
                    "type": "number" if setting["type"] in ["int", "float"] else "",
                    "valueSources": ["value"],
                }
            }
            if setting["type"] == "select":
                field[setting["property"]]["type"] = "select"
                field[setting["property"]]["fieldSettings"] = { "listValues": setting["options"] }

            return field

        def get_worker_fields(worker_metadata):
            workers = list(
                map(lambda algorithm: algorithm["name"], worker_metadata["value"]))
            subfields = [{
                "worker": {
                    "type": "select",
                    "fieldSettings": {
                        "listValues": workers,
                    },
                    "valueSources": ["value"],
                }
            }]
            subfields += [{
                worker + "_Settings": {
                    "label": worker,
                    "tooltip": "Group of fields",
                    "type": "!struct",
                    "subfields":  OrderedDict(ChainMap(*[get_field(setting) for setting in worker_metadata["value"][index]["settings"]]))
                }
            } for index, worker in enumerate(workers)]

            return {
                "label": worker_metadata["property"],
                "type": "!group",
                "subfields": OrderedDict(ChainMap(*subfields))
            }

        metadata = self.find_settings_metadata()

        fields = [{
            "run_id": {
                "label": "Run ID",
                "type": "text",
            },
            "description": {
                "label": "Description",
                "type": "text",
            },
            "selected_input_files": {
                "label": "Selected Input files",
                "type": "multiselect",
                "fieldSettings": {
                    "showSearch": "true",
                    "listValues": [
                        {"value": file, "title": file}
                        for file in self.find_input_files()
                    ],
                    "allowCustomValues": "false"
                }
            },
            "status": {
                "label": "Status",
                "type": "select",
                "fieldSettings": {
                    "listValues": ["CREATED", "RUNNING", "COMPLETED", "FAILED"],
                },
                "valueSources": ["value"],
            },
            "created_on": {
                "label": "Created on",
                "type": "date",
                "valueSources": ["value"],
                "fieldSettings": {
                    "dateFormat": "DD-MM-YYYY",
                    "validateValue": str('''(val, fieldSettings) => {
                        // example of date validation
                        const dateVal = moment(val, fieldSettings.valueFormat);
                        return dateVal.year() != (new Date().getFullYear()) ? "Please use current year" : null;
                    }'''),
                },
            },
            "creator": {
                "label": "Created by",
                "type": "select",
                "valueSources": ["value"],
                "fieldSettings": {
                    "asyncFetch": "simulatedAsyncFetch",
                    "useAsyncSearch": "true",
                    "useLoadMore": "true",
                    "forceAsyncSearch": "false",
                    "allowCustomValues": "false"
                },
            }
        }]
        fields += [{
            worker_list_field: get_worker_fields(metadata[index])
        } for index, worker_list_field in enumerate(["lost_samples_masks", "reconstructed_tracks", "output_analysis"])]
        fields.reverse()
        return OrderedDict(ChainMap(*fields))

    def save_filter(self, filter: Filter, user: User):
        ConfigurationService._logger.info("Saving filter ...")
        matching_filters = self.find_filters({"name": filter.name}, user)
        if matching_filters and len(matching_filters) > 0:
            raise DuplicatedKeyException(
                f"A filter with name '{filter.name}' already exists!")
        persisted_filter = self.filter_repository.add(filter, user)
        filter._id = str(persisted_filter.inserted_id)
        return filter

    def find_filters(self, filter: Filter, user: User):
        ConfigurationService._logger.info("Loading filters ...")
        filters = self.filter_repository.find_by_query(filter, user=user)
        return filters["data"]

    def find_input_files(self):
        self._logger.info("Retrieving input files ...")
        path_manager = PathManager(self.root_folder)
        result = [os.path.basename(original_track)
                  for original_track in path_manager.get_original_tracks()]
        return result

    def upload_audio_files(self, file, total_file_size: int, total_chunks: int, current_chunk: int, offset: int):
        self._logger.info("Uploading file ...")
        save_path = os.path.join(
            self.root_folder, secure_filename(file.filename))

        # If the file already exists it's ok if we are appending to it,
        # but not if it's new file that would overwrite the existing one
        if os.path.exists(save_path) and current_chunk == 0:
            # 400 and 500s will tell dropzone that an error occurred and show an error
            raise UploadException('File already exists')

        # FIXME - check for duplicates

        try:
            with open(save_path, 'ab') as f:
                f.seek(int(offset))
                f.write(file.stream.read())
        except OSError:
            # log.exception will include the traceback so we can see what's wrong
            self._logger.exception('Could not write to file')
            raise UploadException(
                "Not sure why, but we couldn't write the file to disk")

        if current_chunk + 1 == total_chunks:
            # This was the last chunk, the file should be complete and the size we expect
            if os.path.getsize(save_path) != int(total_file_size):
                self._logger.error(f"File {file.filename} was completed, "
                                   f"but has a size mismatch."
                                   f"Was {os.path.getsize(save_path)} but we"
                                   f" expected {total_file_size} ")
                raise UploadException('Size mismatch')
            else:
                self._logger.info(
                    f'File {file.filename} has been uploaded successfully')
        else:
            self._logger.debug(f'Chunk {current_chunk + 1} of {total_chunks} '
                               f'for file {file.filename} complete')
            
    def validate_worker(worker: Worker):
        pass


class UploadException(Exception):

    def __init__(self, message):
        super().__init__(message)


class DuplicatedKeyException(Exception):

    def __init__(self, message):
        super().__init__(message)
        
class ValidationException(Exception):

    def __init__(self, message):
        super().__init__(message)
