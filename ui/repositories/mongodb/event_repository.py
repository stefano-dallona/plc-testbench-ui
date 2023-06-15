import logging
from pymongo import MongoClient
from typing import List

from ui.repositories.mongodb.base_repository import BaseMongoRepository

from ...config.app_config import *
from ...models.event import Event

class EventRepository(BaseMongoRepository):
    
    def __init__(self):
        super().__init__()

        self.collection_metadata = { 'name': 'Events' }
        self.__create_collection__(self.collection_metadata)
    
    def __create_collection__(self, collection):
        if not collection['name'] in self.db.list_collection_names():
            self.logger.info(f"Collection {collection['name']} missing. Creating ...")
            self.db.create_collection(
                collection['name']
            )
            self.logger.info(f"Collection {collection['name']} created")
        else:
            self.logger.info(f"Collection {collection['name']} already exists")
        
    def add(self, item: Event):
        return self.db.get_collection(self.collection_metadata["name"]).insert_one(item.__dict__)
        
    def get(self, **kwargs) -> Event:
        return Event(kwargs=self.db.get_collection(self.collection_metadata["name"]).find_one({'_id': kwargs["id"]}))
    
    def find_by_query(self,
                      query,
                      projection = None,
                      pagination = None) -> List[Event]:
        collection = self.db.get_collection(self.collection_metadata["name"])
        totalRecords = collection.count_documents(query)
        query = collection  \
            .find(query, projection=projection)
        cursor =  query if pagination == None else query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        return {
            'data': map(lambda dict: Event(kwargs=dict), list(cursor)),
            'totalRecords': totalRecords
        }
    
    def update(self, item):
        pass
    
    def delete(self, item):
        pass