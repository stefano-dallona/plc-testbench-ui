import logging
from pymongo import MongoClient
from pymongo.database import Database
from typing import List

from ui.repositories.mongodb.base_repository import BaseMongoRepository

from ...config.app_config import *
from ...models.event import Node
from ...models.user import User

views = [
    {
        'name': 'RunView',
        'on': 'runs',
        'pipeline': [
            {'$unionWith': {'coll': "OriginalTrackNode", 'pipeline': []}},
            {'$unionWith': {'coll': "LostSamplesMaskNode", 'pipeline': []}},
            {'$unionWith': {'coll': "ReconstructedTrackNode", 'pipeline': []}},
            {'$unionWith': {'coll': "OutputAnalysisNode", 'pipeline': []}}
        ]
    }
]


class NodeRepository(BaseMongoRepository):

    def __init__(self):
        super().__init__()
        self.collection_metadata = {'name': 'NodeView'}
        self.collection = None
        self.logger = logging.getLogger()
        self.logger.info(f"Repository {__name__} initialized successfully")

    def initialize_database(self, database: Database):
        if self.initialized:
            return

        initialized = False
        for view in views:
            initialized |= self.__create_view__(database, view)

        # to be done only if not connecting to mongodb atlas
        if not config.db_conn_string.startswith("mongodb+srv://"):
            initialized |= self.__create_role_for_views__(database)
            initialized |= self.__grant_find_role_on_views__(database)

        self.initialized = initialized
        self.logger.info(f"Database initialized: {self.initialized}")

    def find_by_id(self,
                   id,
                   projection=None,
                   user=None) -> any:
        return Node(kwargs=super().get_database(user).get_collection(self.collection_metadata["name"]).find_one({'_id': id}))

    def find_by_query(self,
                      query,
                      projection=None,
                      pagination=None,
                      user=None) -> List[Node]:
        collection = super().get_database(user).get_collection(
            self.collection_metadata["name"])
        totalRecords = collection.count_documents(query)
        query = collection  \
            .find(query, projection=projection)
        cursor = query if pagination == None else query \
            .skip(pagination["page"] * pagination["pageSize"]) \
            .limit(pagination["pageSize"])
        return {
            'data': map(lambda dict: Node(kwargs=dict), list(cursor)),
            'totalRecords': totalRecords
        }

    def add(self, item: Node, user):
        pass

    def update(self, item, user):
        pass

    def delete(self, item, user):
        pass
