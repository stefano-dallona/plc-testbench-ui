import uuid
from datetime import datetime
from anytree import *

from .base_model import *

class Event(Serializable):
    def __init__(self,
                 _id: str = None,
                 task_id: str = None,
                 type: str = None,
                 source_id: str = None,
                 data: str = "{}",
                 timestamp: datetime = datetime.now(),
                 **kwargs):
        if _id != None:
            self._id = _id
        self.task_id = task_id
        self.type = type
        self.source_id = source_id
        self.data = data
        self.timestamp = timestamp
        
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def __str__(self):
        return f"event:{self.type}\ndata:{self.data}\nid:{self.task_id}\n\n".replace("'", "\"")