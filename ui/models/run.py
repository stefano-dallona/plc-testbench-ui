import uuid
from datetime import datetime, date
from anytree import *
from typing import List
from enum import Enum

from plctestbench.plc_testbench import PLCTestbench

from .base_model import *

class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

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
                 #run_id: str = None,
                 run_id = None,
                 root_folder: str = "",
                 selected_input_files: list = [],
                 description: str = "",
                 status: RunStatus = RunStatus.CREATED,
                 creator: str = "anonymous",
                 created_on: str = "",
                 #global_settings: dict = dict(),
                 packet_loss_simulators: list = [],
                 plc_algorithms: list = [],
                 output_analysers: list = []):
        self.root_folder = root_folder
        self.run_id = run_id #if run_id != None else str(uuid.uuid4())
        self.selected_input_files = selected_input_files
        self.description = description
        self.created_on = created_on if created_on != "" else str(datetime.now())
        self.creator = creator if creator != None else "anonymous"
        self.status = status
        self.progress = 0
        #self.global_settings = global_settings
        self.original_audio_tracks = list(map(lambda x: (x, str(uuid.uuid4())), selected_input_files))
        self.packet_loss_simulators = list(map(lambda x: (x[0].__name__, x[1]), packet_loss_simulators))
        self.plc_algorithms = list(map(lambda x: (x[0].__name__, x[1]), plc_algorithms))
        self.output_analysers = list(map(lambda x: (x[0].__name__, x[1]), output_analysers))
