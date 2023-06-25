import logging
import json
import uuid

from functools import partial
from typing import List
from pymongo import MongoClient

from plctestbench.settings import *

from ...config.app_config import *
from ...models.base_model import *
from ...models.run import *
from ...models.event import *
from ...models.samples import *
from ...models.user import *

class BaseMongoRepository:
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    __default_pagination__ = { 'page': 0, 'pageSize': 10 }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = MongoClient(config.db_conn_string).get_database(config.db_name)
        self.admin = MongoClient(config.db_conn_string).get_database("admin")
    
    def add(self, item: any):
        pass
     
    def update(self, item):
        pass
    
    def delete(self, id):
        pass
    
    def find_by_id(self,
                   id,
                   projection = None) -> any:
        pass
    
    def find_by_filter(self,
                          filters = dict(),
                          projection = None,
                          pagination = __default_pagination__) -> List[any]:
        pass

    @staticmethod
    def fromDict(data, classname_field = "classname"):
        if isinstance(data, list):
            return list(map(lambda x : BaseMongoRepository.fromDict(x, classname_field), data))
        elif isinstance(data, dict):
            if not classname_field in data.keys():
                return data
            else:
                classname = globals()[data[classname_field]]
                if classname != None:
                    obj = classname()
                    for key, value in data.items():
                        setattr(obj, key, BaseMongoRepository.fromDict(value, classname_field))
                    return obj
                else:
                    return data

        else:
            return data
        
    @staticmethod
    def toDict(item: any, classname_field: str = "classname", id_field: str = None):
        
        def encode(classname_field, id_field, o):
            return dict(list(o.__dict__.items()) + list(
            {
                "_id" : o.__dict__[id_field] if id_field != None and id_field in o.__dict__.keys() else str(uuid.uuid4()),
                classname_field: type(o).__name__
            }.items()))
        
        class_encoder = partial(encode, classname_field, id_field)
        data = json.loads(json.dumps(item, default=class_encoder))
        return data
