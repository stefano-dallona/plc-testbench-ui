import uuid
from datetime import datetime
from anytree import *
from typing import List

from .base_model import *

class RunExecution(Serializable):
    def __init__(self,
                 run_id: str,
                 hierarchy: List[Node]=[],
                 seed=datetime.now().timestamp(),
                 execution_id:str = str(uuid.uuid4)):
        self.run_id = run_id
        self.hierarchy = hierarchy
        self.seed = seed
        self.execution_id = execution_id

class Run(Serializable):
    def __init__(self,
                 run_id):
        self.run_id = run_id
        self.executions = {}
        
    def addExecution(self, execution: RunExecution):
        self.executions[execution.execution_id] = execution
        
