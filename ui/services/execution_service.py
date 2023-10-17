
from anytree import *

import os
import logging
import json

from plctestbench.node import *
from plctestbench.data_manager import *
from plctestbench.path_manager import *

from ..config.app_config import *
from .plctestbench_service import EccTestbenchService, announcer, get_execution_last_event
from ..models.run import *
from ..models.event import Event
from ..repositories.pickle.run_repository import RunRepository
from ..repositories.mongodb.event_repository import EventRepository
from ..services.configuration_service import ConfigurationService
from ..testbench.customization import OriginalTrackNode as CustomOriginalTrackNode

event_repository = EventRepository()

class ExecutionService:
    
    _logger = logging.getLogger(__name__)
    
    def __init__(self, ecctestbench_service: EccTestbenchService, run_repository: RunRepository):
        self.ecctestbench_service = ecctestbench_service
        self.run_repository = run_repository
        
    def get_execution_hierarchy(self, run_id, execution_id, user) -> List[Node]:
        run = self.ecctestbench_service.load_run(run_id, user)
        if run == None:
            return None
        self._logger.info(f"Loaded run for {run_id} ...")
        execution = RunExecution(run_id=run_id, hierarchy=[])
        
        #for file_tree in run.__ecctestbench__.data_manager.get_data_trees():
        plc_testbench = self.ecctestbench_service.build_testbench_from_run(run, user, readonly=True)
        for file_tree in plc_testbench.data_manager.get_data_trees():
            execution.hierarchy.append(self.__build_output_hierarchy__(file_tree, status=run.status))
        return execution.hierarchy
    
    def get_runs(self, pagination, user) -> List[Run]:
        return self.run_repository.find_by_filter(filters={}, projection=None, pagination=pagination, user=user)
    
    def get_execution_events(self, task_id, run_id, execution_id, last_event_id = None, user = None):
        try:
            if (last_event_id != None):
                event = get_execution_last_event(last_event_id, user)
                yield str(event)
            
            messages = announcer.listen(task_id)  # returns a queue.Queue
            while True:
                try:
                    msg = messages.get()  # blocks until a new message arrives
                    msg_entries = map(lambda x: (x[0].strip(), x[1].strip()), map(lambda x: x.split(":", 1), filter(lambda x: len(x.strip()) > 0, msg.split("\n"))))
                    message = dict(msg_entries)
                    data = json.loads(message["data"])
                    event = Event(type=message["event"],
                        source_id=data["nodeid"],
                        task_id=data["task_id"],
                        data=data)
                    #event_repository.add(event, user)
                    messages.task_done()
                    yield str(event)
                    self._logger.info(f"Received event {event}")
                except Exception as e:
                    self._logger.info(f"An exception occurred: {str(e)}")
        except GeneratorExit as e:
            announcer.disconnect(task_id)
            self._logger.error(f"SSE generator: exited: {str(e)}")
        except Exception as e:
            self._logger.error(f"SSE generator: an exception occurred: {str(e)}")
        finally:
            #announcer.disconnect(task_id)
            pass

    def find_last_run_event(self, run_id, last_event_id, user):
        query = { '_id': last_event_id }
        last_event = event_repository.find_by_query(query, user)
        return last_event
    
    def find_events_after_last(self, run_id, last_event_id, user):
        query = { '_id': last_event_id, 'data.run_id': run_id }
        events = event_repository.find_by_query(query, user)
        return events

    @staticmethod
    def __build_output_hierarchy__(node: Node, parent: Node = None, status: RunStatus = RunStatus.CREATED) -> Node:
        name = node.__class__.__name__
        type = node.__class__.__name__
        file = node.absolute_path if node.absolute_path != None else ""

        if isinstance(node, OriginalTrackNode) or isinstance(node, CustomOriginalTrackNode):
            name = os.path.basename(file) if file != "" else name
            file += ".wav"
            category = ""
        elif isinstance(node, LostSamplesMaskNode):
            name = node.worker.__class__.__name__
            file += ".npy"
            category = ""
        elif isinstance(node, ReconstructedTrackNode):
            name = node.worker.__class__.__name__
            file += ".wav"
            category = ""
        elif isinstance(node, OutputAnalysisNode):
            name = node.worker.__class__.__name__
            file += ".pickle"
            category = ConfigurationService.get_output_analyser_category(node.worker.__class__)
        node_id = str(node.get_id())
        print("level:%d, name:%s, type:%s, uuid:%s, file:%s" % (node.depth, name, type, node_id, file))
        transformed_node = Node(name, parent=parent, parent_id=parent.uuid if parent != None else None, type=type, file=file, uuid=node_id, category=category, status=status, worker_settings=node.worker.settings.settings)
        #transformed_node = Node(name, parent=parent, parent_id=parent.get_id() if parent != None else None, type=type, file=file, uuid=node_id, category=category)
        transformed_node.children = [ExecutionService.__build_output_hierarchy__(child, transformed_node, status) for child in node.children]
        return transformed_node
