import logging
from pymongo import MongoClient
from pymongo.database import Database
from bson.objectid import ObjectId
from typing import List

from ui.repositories.mongodb.base_repository import BaseMongoRepository

from ...config.app_config import *
from ...models.filter import Filter
from ...models.user import User

class FilterRepository(BaseMongoRepository):
    
    def __init__(self):
        super().__init__()

        self.collection_metadata = { 'name': 'Filters' }
        
    def initialize_database(self, database: Database):
        if self.initialized:
            return
        
        initialized = False
        initialized |= self.__create_collection__(database, self.collection_metadata["name"])
        
        self.initialized = initialized
        
    def add(self, item: Filter, user):
        return super().get_database(user).get_collection(self.collection_metadata["name"]).insert_one(item.__dict__)
        
    def find_by_id(self,
                   id,
                   projection = None,
                   user = None) -> any:
        return Filter(kwargs=super().get_database(user).get_collection(self.collection_metadata["name"]).find_one({'_id': id}))
    
    def find_by_query(self,
                      query,
                      projection = None,
                      pagination = None,
                      user = None) -> List[Filter]:
        collection = super().get_database(user).get_collection(self.collection_metadata["name"])
        totalRecords = collection.count_documents(query)
        query = collection  \
            .find(query, projection=projection)
        cursor =  query if pagination == None else query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        return {
            'data': list(map(lambda dict: Filter(**dict), list(cursor))),
            'totalRecords': totalRecords
        }
    
    def update(self, item, user):
        pass
    
    def delete(self, item, user):
        collection = super().get_database(user).get_collection(self.collection_metadata["name"])
        result = collection.delete_one({ "_id": ObjectId(item._id) })
        return result.deleted_count > 0