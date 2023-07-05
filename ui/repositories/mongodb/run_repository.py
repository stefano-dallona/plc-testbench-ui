from typing import List
import json
from pymongo.database import Database

from plctestbench.database_manager import *
from plctestbench.utils import *

from ...config.app_config import *
from ...models.run import Run
from ...models.user import User
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
    },
    {
        'name': 'RunView',
        'on': 'runs',
        'pipeline': [
            {
                '$project': {
                    '_id': 1,
                    'selected_input_files': {
                        '$map': {
                        'input': "$nodes",
                        'as': "node",
                        'in': "$$node._id"
                        }
                    },
                    "workers": 1,
                    "nodes": 1
                }
            },
            {
                '$lookup': {
                    'from': "OriginalTrackNode",
                    'localField': "selected_input_files",
                    'foreignField': "_id",
                    'as': "selected_input_files"
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'selected_input_files': {
                        '$map': {
                        'input': "$selected_input_files",
                        'as': "input_file",
                        'in': { '$last': { '$split': [ "$$input_file.filename", "\\" ] } }
                        }
                    },
                    "workers": {
                        "$reduce": {
                        "input": '$workers',
                        "initialValue": [],
                        "in": {"$concatArrays": ['$$value', '$$this']}
                        }
                    },
                    "nodes": 1
                }
            }
        ]
    }
]

class RunRepository(BaseMongoRepository):
    
    def __init__(self):
        super().__init__()
        self.collection_metadata = { 'name' : 'OriginalTrack-3' }
        self.collection = collection
          
    def initialize_database(self, database: Database):
        if self.initialized:
            return
        
        initialized = False
        initialized |= self.__create_collection__(database, self.collection)
        
        for view in views:
            initialized |= self.__create_view__(database, view)
        
        initialized |= self.__create_role_for_views__(database)
        initialized |= self.__grant_find_role_on_views__(database)
        
        self.initialized = initialized
        
    def get_plc_database_manager(self, user: User):
        return DatabaseManager(ip=db_host, port=db_port, username=db_username, password=db_password, user=user.__dict__)
        
    def add(self, item: Run, user: User):
        result = self.get_database(user).get_collection(self.collection).insert_one(BaseMongoRepository.toDict(item, "classname", "run_id"))
        return result.inserted_id
        
    def find_by_id(self, id: str, user: User) -> Run:
        #data = self.db.get_collection(self.collection_metadata["name"]).find_one({'_id': id })
        data = self.get_database(user).get_collection("RunView").find_one({'_id': int(id) })
        #data = self.get_plc_database_manager(user).get_run(int(id))
        data["run_id"] = data["_id"]
        data["classname"] = "Run"
        data["creator"] = "anonymous"
        data["root_folder"] = config.data_dir
        data["selected_input_files"] = sorted(data["selected_input_files"])
        return BaseMongoRepository.fromDict(data)
    
    def find_by_filter(self,
                      filters,
                      projection,
                      pagination,
                      user: User) -> List[Run]:
        #collection = self.db.get_collection(self.collection_metadata["name"])
        #collection = self.get_database(user).get_collection(self.collection)
        collection = self.get_database(user).get_collection("RunView")
        totalRecords = collection.count_documents(filters)
        query = collection  \
            .find(filters, projection=projection)
        cursor =  query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        data = list(cursor)
        
        enriched_data = list(map(lambda x: dict(x, classname="Run", creator=user.email, run_id=str(x["_id"])), data))
        typed_data = list(map(BaseMongoRepository.fromDict, enriched_data))
        
        return {
            'data': typed_data,
            'totalRecords': totalRecords
        }
    
    def update(self, item: Run, user: User) -> int:
        deleteCount = self.delete(item, user)
        if deleteCount >= 0:
            id = self.add(item, user)
            return 1
        else:
            return 0
    
    def delete(self, item: Run, user) -> int:
        result = self.get_database(user).get_collection(self.collection).delete_one({ '_id' : item.run_id })
        return result.deleted_count