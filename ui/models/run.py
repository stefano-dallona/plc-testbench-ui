import uuid
from datetime import datetime, date
from anytree import *
from typing import List
from enum import Enum

from plctestbench.plc_testbench import PLCTestbench

from .base_model import *

RunStatus = Enum('RunStatus', ['CREATED', 'RUNNING', 'COMPLETED', 'FAILED'], start=1)

class RunExecution(Serializable):
    def __init__(self,
                 run_id: str,
                 hierarchy: List[Node] = [],
                 seed=datetime.now().timestamp(),
                 execution_id:str = str(uuid.uuid4)):
        self.run_id = run_id
        self.hierarchy = hierarchy
        self.seed = seed
        self.execution_id = execution_id

class Run(Serializable):
    def __init__(self,
                 plc_testbench: PLCTestbench,
                 selected_input_files: list,
                 description: str = "",
                 status: RunStatus = RunStatus.CREATED,
                 creator: str = "anonymous",
                 created_on: str = ""):
        self.__ecctestbench__ = plc_testbench
        self.run_id = plc_testbench.uuid
        self.selected_input_files = selected_input_files
        self.description = description
        self.created_on = created_on if created_on != "" else str(datetime.now())
        self.creator = creator if creator != None else "anonymous"
        self.status = status
