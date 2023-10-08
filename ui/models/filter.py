import uuid
from datetime import datetime
from anytree import *

from .base_model import *

class Filter(Serializable):
    def __init__(self,
                 _id: str = None,
                 name: str = None,
                 query: str = None,
                 **kwargs):
        if _id != None:
            self._id = str(_id)
       
        self.name = name
        self.query = query
        
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        assert self.name, "name is required"
        assert self.query, "query is required"