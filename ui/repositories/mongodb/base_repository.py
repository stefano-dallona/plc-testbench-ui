import logging
import json
import uuid

from functools import partial
from typing import List
from abc import ABC, abstractmethod
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo.database import Database

from plctestbench.settings import *
from plctestbench.utils import *

from ...config.app_config import *
from ...models.base_model import *
from ...models.run import *
from ...models.event import *
from ...models.samples import *
from ...models.user import *

class Singleton (type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class BaseMongoRepository(metaclass=Singleton):
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    __default_pagination__ = { 'page': 0, 'pageSize': 10 }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(config.db_conn_string)
        #self.db = self.client.get_database(config.db_name)
        self.admin = self.client.get_database("admin")
        self.initialized = False
    
    def get_database(self, user: User):
        database = self.client.get_database(escape_email(user.email))
        self.initialize_database(database)
        return database
    
    @abstractmethod
    def initialize_database(self, database):
        pass
        
    def __create_collection__(self, database: Database, collection) -> bool:

        if not collection in database.list_collection_names():
            self.logger.info(f"Collection {collection} missing. Creating ...")
            database.create_collection(
                collection
            )
            self.logger.info(f"Collection {collection} created")
        else:
            self.logger.info(f"Collection {collection} already exists")
        return True
    
    def __create_view__(self, database: Database, view) -> bool:
        if not view['name'] in database.list_collection_names():
            self.logger.info(f"View {view['name']} missing. Creating ...")
            database.create_collection(
                view['name'],
                viewOn = view['on'],
                pipeline = view['pipeline']
            )
            self.logger.info(f"View {view['name']} created")
        else:
            self.logger.info(f"View {view['name']} already exists")
        return True
            
    def __grant_find_role_on_views__(self, database: Database) -> bool:
        self.logger.info(f"Granting readViewCollection role to {db_username} ...")
        self.admin.command("grantRolesToUser", db_username, roles=["readViewCollection"])
        return True
    
    def __create_role_for_views__(self, database: Database) -> bool:
        try:
            self.admin.command(
                'createRole', 'readViewCollection',
                privileges=[{
                    'actions': ['find'],
                    'resource': {'db': database.name, 'collection': 'system.views'}
                }],
                roles=[])
            return True
        except OperationFailure as exception:
            self.logger.error(exception)
            return self.__update_role_for_views__(database)

    
    def __update_role_for_views__(self, database: Database) -> bool:
        try:
            self.admin.command(
                'grantPrivilegesToRole', 'readViewCollection',
                privileges=[{
                    'actions': ['find'],
                    'resource': {'db': database.name, 'collection': 'system.views'}
                }])
            return True
        except OperationFailure as exception:
            self.logger.error(exception)
            return False
    
    def add(self, item: any, user: User):
        pass
     
    def update(self, item: any, user: User):
        pass
    
    def delete(self, id, user: User):
        pass
    
    def find_by_id(self,
                   id,
                   projection = None,
                   user = None) -> any:
        pass
    
    def find_by_filter(self,
                          filters = dict(),
                          projection = None,
                          pagination = __default_pagination__,
                          user: User = None) -> List[any]:
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
