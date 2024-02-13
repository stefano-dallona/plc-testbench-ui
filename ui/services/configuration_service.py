from werkzeug.utils import secure_filename

import logging
import os
import uuid as Uuid
import inspect
import typing
import functools
import typing_extensions
import re
from operator import itemgetter
from itertools import groupby, chain
from collections import ChainMap, OrderedDict
from enum import Enum
from bson.objectid import ObjectId
from typing import List, Dict

from plctestbench.worker import *
from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.path_manager import *
from plctestbench.node import *
from plctestbench.settings import *
#from plctestbench.crossfade import *

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
                         if ancestor in Worker.__subclasses__()
                         #if ancestor in [PacketLossSimulator, PLCAlgorithm, OutputAnalyser, Crossfade, MultibandCrossfade]
                         ]:
            return ancestor
        return None
    
    @staticmethod
    def get_subclasses_recursively(cls) -> List[type]:
        subclasses = cls.__subclasses__()
        for subclass in subclasses:
            if subclass.__subclasses__() != []:
                subclasses.extend(ConfigurationService.get_subclasses_recursively(subclass))
        return subclasses

    @staticmethod
    def get_value_type(property, clazz):
        class_constructor_annotations = inspect.getfullargspec(clazz.__init__).annotations
        value_type = class_constructor_annotations[property] if property in class_constructor_annotations.keys() else None
        return value_type

    @staticmethod
    def find_settings_metadata(settings_list: List[Settings] = None, modified_setting: str = None, new_value = None):
        cs = ConfigurationService
        ConfigurationService._logger.info("Retrieving settings metadata ...")
        
        def instantiate_settings(cls):
            try:
                return cls()
            except Exception as e:
                ConfigurationService._logger.info("Could not instantiate %s: %s", cls.__name__, str(e))
                      
        def get_modifier(property, clazz) -> callable:
            modifier_name = "set_" + property
            return getattr(clazz, modifier_name) if hasattr(clazz, modifier_name) and callable(getattr(clazz, modifier_name)) else None
        
        def has_modifier(property, clazz) -> bool:
            return get_modifier(property, clazz) is not None
        
        def update_setting(settings, modified_setting, new_value):
            modifier = get_modifier(modified_setting, type(settings))
            return modifier(settings, new_value)
        
        def get_collection_item_type(property, clazz):
            class_constructor_annotations = inspect.getfullargspec(clazz.__init__).annotations
            property_name = re.sub(r'\.\d+$', '', property)
            if property_name in class_constructor_annotations.keys():
                property_annotation = class_constructor_annotations[property_name]
                property_annotation_tuple = typing_extensions.get_args(property_annotation)
                collection_item_type = property_annotation_tuple[-1] if len(property_annotation_tuple) > 0 else None
                if collection_item_type is None and property_annotation is not None:
                    m = re.search('.*\[(\w+Settings)\].*', property_annotation)
                    if m is not None and len(m.groups()) > 0:
                        return type(globals()[m.group(1)]())
                return collection_item_type
            return None
        
        def is_settings_subclass(clazz):
            return hasattr(clazz, "__mro__") and Settings in clazz.__mro__
        
        def get_settings_subclasses_metadata(property, value_type, children, root_class = None):
            subclasses_instances = [subclass() for subclass in ConfigurationService.itersubclasses(value_type) if subclass != root_class ]
            safe_children_list = list(filter(lambda x: type(x) != root_class, children))
            return  {
                "property": property,
                "value": [
                    {
                        "name": type(child).__name__,
                        "settings": [
                            get_settings_metadata(property, value, child)
                            for property, value in child.settings.items()
                            if not property.startswith("__")
                        ],
                        "options": [
                            {
                                "name": type(subclass).__name__,
                                "settings": [
                                    get_settings_metadata(property, value, subclass)
                                    for property, value in subclass.settings.items()
                                    if not property.startswith("__")
                                ]
                            }
                            for subclass in subclasses_instances
                        ]
                    }
                    for child in safe_children_list
                ],
                "valueType": "settingsList",
                "mandatory": True,
                "editable": False
            }
            
        def convert_value(value):
            if type(value).__name__ == 'list':
                return ",".join([str(val) for val in value]) if len(value) > 0 else []
            elif type(value) == Uuid.UUID:
                return str(value)
            return value
        
        def get_nested_type_by_value_type(value_type):
            nested_type = value_type.__args__[0] if value_type is not None and hasattr(value_type, "__args__") and len(getattr(value_type, "__args__")) > 0 else None
            return nested_type

        def get_settings_metadata(property, value, clazz, value_type = None, root_class = None):
            inferred_value_type = None
            if isinstance(value, Enum):
                return {
                    "property": property,
                    "value": value.value,
                    "valueType": "select",
                    "options": [
                        member.value for member in type(value)],
                    "mandatory": True,
                    "editable": clazz is None or ConfigurationService.get_value_type(property, clazz) is not None,
                    "is_modifier": has_modifier(property, clazz)
                }
            elif isinstance(value, Settings):
                inferred_value_type = ConfigurationService.get_value_type(property, clazz)
                return get_settings_subclasses_metadata(property, inferred_value_type, value, root_class)
            elif isinstance(value, list):
                inferred_value_type = value_type if value_type is not None else get_collection_item_type(property, clazz)
                if inferred_value_type and is_settings_subclass(inferred_value_type):
                    return get_settings_subclasses_metadata(property, inferred_value_type, value, root_class)
            elif isinstance(value, dict):
                inferred_value_type = get_collection_item_type(property, clazz)
                nested_value_type = get_nested_type_by_value_type(inferred_value_type)
                return {
                    "property": property,
                    "valueType": "dictionary",
                    "value": [
                        get_settings_metadata(str(entryKey), entryValue, None, nested_value_type if nested_value_type is not None else inferred_value_type, root_class)
                        for entryKey, entryValue in value.items()
                    ],
                    "mandatory": True,
                    "editable": False,
                    "is_modifier": has_modifier(property, clazz)
                }

            return {
                "property": property,
                "value": convert_value(value),
                "valueType": type(value).__name__,
                "nestedType": inferred_value_type.__name__ if inferred_value_type is not None else "",
                "mandatory": True,
                "editable": clazz is None or ConfigurationService.get_value_type(property, clazz) is not None,
                "is_modifier": has_modifier(property, clazz)
            }

        settings_instances = [(instantiate_settings(cls), cs.get_worker_class(cls), cs.get_worker_base_class(cs.get_worker_class(cls))) for cls in ConfigurationService.itersubclasses(Settings)
                             if cs.get_worker_base_class(cs.get_worker_class(cls)) and instantiate_settings(cls)] if settings_list == None or settings_list == [] else [(settings, cs.get_worker_class(settings.__class__), cs.get_worker_base_class(cs.get_worker_class(settings.__class__))) for settings in settings_list]
        
        if modified_setting is not None and new_value is not None:
            assert len(settings_instances) == 1, "Only one settings instance can be modified at a time!"
            settings_tuple = settings_instances[0]
            if has_modifier(modified_setting, type(settings_tuple[0])):
                settings_instances[0] = (update_setting(settings_tuple[0], modified_setting, new_value), settings_tuple[1], settings_tuple[2])

        metadata = [
            {
                "property": category.__name__,
                "value": [
                    {
                        "uuid": str(Uuid.uuid4()),
                        "name": settings[1].__name__,
                        "settings": [
                            get_settings_metadata(property, value, settings[0].__class__, value_type=None, root_class=settings[0].__class__)
                            for property, value in settings[0].settings.items() if not property.startswith("__") and ConfigurationService.get_value_type(property, settings[0].__class__) is not None
                        ],
                        "doc": settings[1].__doc__
                    } for settings in list(settingsMetadata)]
            } for category, settingsMetadata in groupby(settings_instances, key=itemgetter(2))
        ]
        return metadata
    
    @staticmethod
    def validate_settings(settings_list: List[Settings] = None) -> List[str]:
        try:
            configuration_map = ConfigurationService.parse_settings_from_json(settings_list)
            for configuration in chain(*filter(None, configuration_map.values())):
                settings = configuration[1]
                if hasattr(settings, "__validate__") and callable(getattr(settings, "__validate__")):
                    settings.__validate__()
            return []
        except Exception as e:
            return [str(e)]
    
    @staticmethod    
    def get_conversion_function(value_type, settings, setting_value, setting_name: str = None, settings_class = None):
        
        def convert_to_base_value(setting_name, value_type, value):
            try:
                return globals()['__builtins__'][value_type](value)
            except:
                raise ConversionException("{setting_name} must be of type {value_type}".format(setting_name=setting_name, value_type=value_type))
        
        def list_conversion(setting_name, nested_type, value):
            list_values = (value.split(",") if value.strip() != "" else []) if type(value) is str else value
            return [convert_to_base_value(setting_name, nested_type, value) if nested_type is not None and nested_type.strip() != "" else value for value in list_values]
        
        try:
            if value_type == "settingsList" :
                return ConfigurationService.settingsList_conversion
            elif value_type == "list" :
                nested_type = setting_value["nestedType"] if setting_value["nestedType"] is not None else str
                return lambda x: list_conversion(setting_name, nested_type, x)
            elif value_type == "dictionary" :
                return ConfigurationService.dictionary_conversion
            elif value_type == "select" :
                return ConfigurationService.get_value_type(setting_name, settings_class) if setting_name and settings_class else type(settings.settings[setting_value["property"]])
            elif value_type == "bool" :
                return lambda x: x == 'true'
            else:
                return lambda value: convert_to_base_value(setting_name, value_type, value)
        except:
            return lambda x: x
    
    @staticmethod
    def copy_attributes(settings, json_dict):
        for setting_data in json_dict["settings"]:
            try:
                setting = setting_data["data"] if "data" in setting_data.keys() else setting_data
                value = setting_data if setting["valueType"] in ["settingsList", "dictionary"] else setting["value"]
                setting_name = setting["property"]
                conversion_function = ConfigurationService.get_conversion_function(setting["valueType"], settings, setting, setting_name)
                value = conversion_function(value)
                if (hasattr(settings, "settings") and type(settings.settings) is dict):
                    settings.settings[setting_name] = value
                else:
                    setattr(settings, setting_name, value)
            except ConversionException as e:
                raise e
            except Exception as e:
                #raise Exception("Could not set property {property} of type {value_type} on Settings".format(property=setting["property"], value_type=setting["valueType"]))
                ConfigurationService._logger.info(
                    "Could not set property %s of type %s on Settings", setting["property"], setting["valueType"])

    
    @staticmethod 
    def settingsList_conversion(setting_data):
        settings = [ globals()[child["data"]["value"]]() for child in setting_data["children"]]
        for index, setting in enumerate(settings):
            ConfigurationService.copy_attributes(setting, { "settings" : [ property for property in setting_data["children"][index]["children"] ] })
        return settings
    
    @staticmethod
    def dictionary_conversion(setting_data):
        return {
            property["data"]["property"]: ConfigurationService.get_conversion_function(property["data"]["valueType"], None, property["data"])(property if property["data"]["valueType"] in ["settingsList", "dictionary"] else property["data"]["value"])
            for property in setting_data["children"]
        }
    
    @staticmethod 
    def parse_settings_from_json(json_dict) -> dict:

        configuration_map = {
            InputFileSelection: None,
            # GlobalSettings: [],
            PacketLossSimulator: [],
            PLCAlgorithm: [],
            OutputAnalyser: []
        }

        def parse_configuration(configuration_map, json_dict) -> dict:
            worker_name = json_dict["name"].replace(" ", "")
            worker_constructor = globals(
            )[worker_name] if worker_name in globals() else None
            worker_settings_name = worker_name + \
                "Settings" if not worker_name.endswith(
                    "Settings") else worker_name
            worker_settings_constructor = globals(
            )[worker_settings_name] if worker_settings_name in globals() else None
            worker_settings = worker_settings_constructor(
            ) if worker_settings_constructor != None else json_dict["settings"]
            worker_base = worker_constructor.__base__ if worker_constructor != None \
                and worker_constructor.__base__ != object \
                and worker_constructor.__base__ != Settings \
                else None
            worker_base = ConfigurationService.get_worker_base_class(
                worker_constructor)
            worker_key = worker_base if worker_base != None else worker_constructor
            worker_id = str(uuid.uuid4())

            if worker_settings_constructor != None:
                ConfigurationService.copy_attributes(worker_settings, json_dict)
            if isinstance(configuration_map[worker_key], list):
                configuration_map[worker_key].extend([(worker_constructor, worker_settings, worker_id) if worker_settings_constructor !=
                                                     None and worker_constructor != worker_settings.__class__ else worker_settings])
            else:
                configuration_map[worker_key] = worker_settings
            return configuration_map

        configuration_map = functools.reduce(parse_configuration, json_dict, configuration_map)
        return configuration_map

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

    def delete_filter(self, filter_id: str, user: User) -> bool:
        ConfigurationService._logger.info("Deleting filter ...")
        matching_filters = self.find_filters({"_id": ObjectId(filter_id)}, user)
        if (not matching_filters) or len(matching_filters) == 0:
            raise KeyNotFoundException(
                f"No filter with id '{filter_id}' was found!")
        result = self.filter_repository.delete(matching_filters[0], user)
        return result

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

class InputFileSelection:
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
   
class KeyNotFoundException(Exception):

    def __init__(self, message):
        super().__init__(message)

class ConversionException(Exception):

    def __init__(self, message):
        super().__init__(message)