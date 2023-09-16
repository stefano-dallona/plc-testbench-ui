import uuid
from datetime import datetime
from anytree import *

from .base_model import *

class Node(Serializable):
    def __init__(self,
                 _id: str = None,
                 parent: str = None,
                 **kwargs):
        self._id = _id
        self.parent = parent
        
        for key, value in kwargs.items():
            setattr(self, key, value)