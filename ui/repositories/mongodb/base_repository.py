import logging

from typing import List
from pymongo import MongoClient

from ...config.app_config import *

class BaseMongoRepository:
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    __default_pagination__ = { 'page': 0, 'pageSize': 10 }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = MongoClient(config.db_conn_string).get_database(config.db_name)
    
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
    
    def find_by_predicate(self,
                          predicate,
                          projection = None,
                          pagination = __default_pagination__) -> List[any]:
        pass
    
    def find_by_query(self,
                      query,
                      projection,
                      pagination = __default_pagination__) -> List[any]:
        pass

