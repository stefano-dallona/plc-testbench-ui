from typing import List
import json
import logging
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
        'name': 'RunView',
        'on': 'runs',
        'pipeline': [
            {
            '$addFields': { 'run_id': '', 'description': '', 'classname': 'Run'  }
            },
            {
                '$project': {
                    '_id': 1,
                    'classname': 1,
                    'run_id': "$_id",
                    'description': 1,
                    'status': 1,
                    'creator': "$creator",
                    'created_on': { "$dateToString":{"format":"%Y-%m-%dT%H:%M:%S", "date":"$created_on"}},
                    'selected_input_files': {
                        '$arrayElemAt': ["$workers", 0]
                    },
                    'lost_samples_masks': {
                        '$arrayElemAt': ["$workers", 1]
                    },
                    'reconstructed_tracks': {
                        '$arrayElemAt': ["$workers", 2]
                    },
                    'output_analysis': {
                        '$arrayElemAt': ["$workers", 3]
                    },
                    "nodes": 1
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'classname': 1,
                    'run_id': 1,
                    'description': 1,
                    'status': 1,
                    'creator': 1,
                    'created_on': 1,
                    'selected_input_files': {
                        '$map': {
                            'input': "$selected_input_files",
                            'in': "$$this.settings.filename"
                        }
                    },
                    'lost_samples_masks': {
                        '$map': {
                            'input': "$lost_samples_masks",
                            'in': {
                                '$mergeObjects': [
                                        {
                                            'worker': "$$this.name"
                                        },
                                    "$$this",
                                    "$$this.settings"
                                ]
                            }
                        }
                    },
                    'reconstructed_tracks': {
                        '$map': {
                            'input': "$reconstructed_tracks",
                            'in': {
                                '$mergeObjects': [
                                    {
                                        'worker': "$$this.name"
                                    },
                                    "$$this",
                                    "$$this.settings"
                                ]
                            }
                        }
                    },
                    'output_analysis': {
                        '$map': {
                            'input': "$output_analysis",
                            'in': {
                                '$mergeObjects': [
                                    {
                                        'worker': "$$this.name"
                                    },
                                    "$$this",
                                    "$$this.settings"
                                ]
                            }
                        }
                    },
                    'nodes': 1
                }
            },
            {
                '$project': {
                    'nodes': 0,
                    'selected_input_files.name': 0,
                    'selected_input_files.settings': 0,        
                    'lost_samples_masks.name': 0,
                    'lost_samples_masks.settings': 0,
                    'reconstructed_tracks.name': 0,
                    'reconstructed_tracks.settings': 0,
                    'output_analysis.name': 0,
                    'output_analysis.settings': 0
                }
            }
        ]
    }
]

#_logger = logging.getLogger(__name__)

class RunRepository(BaseMongoRepository):

    def __init__(self):
        super().__init__()
        self.collection_metadata = {'name': 'RunView'}
        self.collection = collection
        self.logger = logging.getLogger()
        self.logger.info(f"Repository {__name__} initialized successfully")

    def initialize_database(self, database: Database):
        if self.initialized:
            return

        initialized = False
        #initialized |= self.__create_collection__(database, self.collection)

        for view in views:
            initialized |= self.__create_view__(database, view)

        # to be done only if not connecting to mongodb atlas
        if not config.db_conn_string.startswith("mongodb+srv://") :
            initialized |= self.__create_role_for_views__(database)
            initialized |= self.__grant_find_role_on_views__(database)

        self.initialized = initialized
        self.logger.info(f"Database initialized: {self.initialized}")

    def get_plc_database_manager(self, user: User):
        return DatabaseManager(ip=db_host, port=db_port, username=db_username, password=db_password, user=user.__dict__)

    def add(self, item: Run, user: User):
        result = self.get_database(user).get_collection(self.collection).insert_one(
            BaseMongoRepository.toDict(item, "classname", "run_id"))
        return result.inserted_id

    def find_by_id(self, id: str, user: User) -> Run:
        data = self.get_database(user).get_collection(
            self.collection_metadata["name"]).find_one({'_id': str(id)})
        #data["run_id"] = data["_id"]
        data["classname"] = "Run"
        #data["creator"] = "anonymous"
        data["root_folder"] = config.data_dir
        data["selected_input_files"] = sorted(data["selected_input_files"])
        return BaseMongoRepository.fromDict(data)

    def find_by_filter(self,
                       filters,
                       projection,
                       pagination,
                       user: User) -> List[Run]:
        collection = self.get_database(user).get_collection(self.collection_metadata["name"])
        totalRecords = collection.count_documents(filters)
        query = collection  \
            .find(filters, projection=projection) \
            .sort("created_on", pymongo.DESCENDING)
        cursor = query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        data = list(cursor)

        typed_data = list(map(BaseMongoRepository.fromDict, data))

        return {
            'data': json.loads(json.dumps(typed_data, default=lambda o: o.__dict__)),
            'totalRecords': totalRecords
        }

    def update(self, item: Run, user: User) -> int:
        pass

    def delete(self, item: Run, user) -> int:
        pass
