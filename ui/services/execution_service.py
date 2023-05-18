
from anytree import *

import os
import logging

from plctestbench.node import *

from .ecctestbench_service import EccTestbenchService, announcer
from ..models.run import *
from ..repositories.run_repository import *


class ExecutionService:
    
    _logger = logging.getLogger(__name__)
    
    def __init__(self, ecctestbench_service: EccTestbenchService, run_repository: RunRepository):
        self.ecctestbench_service = ecctestbench_service
        self.run_repository = run_repository
        
    def get_execution_hierarchy(self, run_id, execution_id) -> List[Node]:
        run = self.ecctestbench_service.load_run(run_id)
        if run == None:
            return None
        self._logger.info(f"Loaded run for {run_id} ...")
        execution = RunExecution(run_id=run_id, hierarchy=[])
        for file_tree in run.__ecctestbench__.data_manager.get_data_trees():
            execution.hierarchy.append(self.__build_output_hierarchy__(file_tree))
        return execution.hierarchy
    
    def get_runs(self) -> List[Run]:
        return self.run_repository.list()
    
    def get_execution_events(self, run_id, execution_id):
        messages = announcer.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg

    @staticmethod
    def __build_output_hierarchy__(node: Node, parent: Node = None) -> Node:
        name = node.__class__.__name__
        type = node.__class__.__name__
        file = node.absolute_path if node.absolute_path != None else ""

        if isinstance(node, OriginalTrackNode):
            name = os.path.basename(file) if file != "" else name
            file += ".wav"
        elif isinstance(node, LostSamplesMaskNode):
            name = node.worker.__class__.__name__
            file += ".npy"
        elif isinstance(node, ReconstructedTrackNode):
            name = node.worker.__class__.__name__
            file += ".wav"
        elif isinstance(node, OutputAnalysisNode):
            name = node.worker.__class__.__name__
            file += ".pickle"
        print("level:%d, name:%s, type:%s, file:%s, uuid:%s" % (node.depth, name, type, file, node.uuid))
        transformed_node = Node(name, parent=parent, parent_id=parent.uuid if parent != None else None, type=type, file=file, uuid=node.uuid)
        transformed_node.children = [ExecutionService.__build_output_hierarchy__(child, transformed_node) for child in node.children]
        return transformed_node
