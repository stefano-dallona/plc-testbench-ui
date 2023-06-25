from typing import List
import json
from pymongo.errors import OperationFailure

from ...config.app_config import *
from ...models.run import Run
from .base_repository import BaseMongoRepository

collection = "Run"
views = [
    {
        'name': 'OriginalTrack-1',
        'on': 'ReconstructedTrackNode',
        'pipeline': [{
            '$graphLookup': {
            'from': "OutputAnalysisNode",
            'startWith': "$_id",
            'connectFromField': "_id",
            'connectToField': "parent",
            'maxDepth': 1,
            'as': "outputAnalysis"
            }
        }]
    },
    {
        'name': 'OriginalTrack-2',
        'on': 'LostSamplesMaskNode',
        'pipeline': [{
            '$graphLookup': {
                'from': "OriginalTrack-1",
                'startWith': "$_id",
                'connectFromField': "_id",
                'connectToField': "parent",
                'maxDepth': 2,
                'as': "reconstructedTracks"
            }
        }]
    },
    {
        'name': 'OriginalTrack-3',
        'on': 'OriginalTrackNode',
        'pipeline': [{
            '$graphLookup': {
                'from': "OriginalTrack-2",
                'startWith': "$_id",
                'connectFromField': "_id",
                'connectToField': "parent",
                'maxDepth': 3,
                'as': "lostSamplesMasks"
            }
        }]
    }
]

class RunRepository(BaseMongoRepository):
    
    def __init__(self):
        super().__init__()
        
        self.collection_metadata = { 'name' : 'OriginalTrack-3' }

        self.collection = collection
        self.__create_collection__(self.collection)
        
        for view in views:
            self.__create_view__(view)
        
        self.__create_role_for_views__()
        self.__grant_find_role_on_views__()
    
    def __create_collection__(self, collection):

        if not collection in self.db.list_collection_names():
            self.logger.info(f"Collection {collection} missing. Creating ...")
            self.db.create_collection(
                collection
            )
            self.logger.info(f"Collection {collection} created")
        else:
            self.logger.info(f"Collection {collection} already exists")
    
    def __create_view__(self, view):
        if not view['name'] in self.db.list_collection_names():
            self.logger.info(f"View {view['name']} missing. Creating ...")
            self.db.create_collection(
                view['name'],
                viewOn = view['on'],
                pipeline = view['pipeline']
            )
            self.logger.info(f"View {view['name']} created")
        else:
            self.logger.info(f"View {view['name']} already exists")
            
    def __grant_find_role_on_views__(self):
        self.admin.command("grantRolesToUser", db_username, roles=["readViewCollection"])
    
    def __create_role_for_views__(self):
        try:
            self.admin.command(
                'createRole', 'readViewCollection',
                privileges=[{
                    'actions': ['find'],
                    'resource': {'db': 'plc_database', 'collection': 'system.views'}
                }],
                roles=[])
        except OperationFailure as exception:
            self.logger.error(exception)
            pass
        
    def add(self, item: Run):
        result = self.db.get_collection(self.collection).insert_one(BaseMongoRepository.toDict(item, "classname", "run_id"))
        return result.inserted_id
        
    def find_by_id(self, id) -> Run:
        #data = self.db.get_collection(self.collection_metadata["name"]).find_one({'_id': id })
        data = self.db.get_collection(self.collection).find_one({'_id': id })
        return BaseMongoRepository.fromDict(data)
    
    def find_by_filter(self,
                      filters,
                      projection,
                      pagination) -> List[Run]:
        #collection = self.db.get_collection(self.collection_metadata["name"])
        collection = self.db.get_collection(self.collection)
        totalRecords = collection.count_documents(filters)
        query = collection  \
            .find(filters, projection=projection)
        cursor =  query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        data = list(cursor)
        return {
            'data': BaseMongoRepository.fromDict(data),
            'totalRecords': totalRecords
        }
    
    def update(self, item: Run) -> int:
        deleteCount = self.delete(item)
        if deleteCount >= 0:
            id = self.add(item)
            return 1
        else:
            return 0
    
    def delete(self, item: Run) -> int:
        result = self.db.get_collection(self.collection).delete_one({ '_id' : item.run_id })
        return result.deleted_count