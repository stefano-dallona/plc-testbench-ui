from typing import List

from ...config.app_config import *
from ...models.run import Run
from .base_repository import BaseMongoRepository

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

        for view in views:
            self.__create_view__(view)
    
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
        
    def add(self, item: Run):
        pass
        
    def get(self, **kwargs) -> Run:
        pass
    
    def find_by_query(self,
                      query,
                      projection,
                      pagination) -> List[Run]:
        collection = self.db.get_collection(self.collection_metadata)
        totalRecords = collection.count_documents(query)
        query = collection  \
            .find(query, projection=projection)
        cursor =  query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        return {
            'data': list(cursor),
            'totalRecords': totalRecords
        }
    
    def update(self, item):
        pass
    
    def delete(self, item):
        pass