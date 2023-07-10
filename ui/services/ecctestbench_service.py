from plctestbench.plc_testbench import *
from plctestbench.settings import *
from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.data_manager import *
from plctestbench.path_manager import *
from plctestbench.node import *
from plctestbench.file_wrapper import *

import os
import logging
from flask import json
from flask_socketio import SocketIO
from datetime import datetime
import uuid
from functools import partial
import math
import queue
import shutil
import functools
import itertools
from tqdm.auto import tqdm as std_tqdm
from threading import Thread
from eventlet import sleep

from ..repositories.pickle.run_repository import RunRepository
from ..config.app_config import *
from ..models.run import *
from ..models.user import *

progress_cache = dict()

class TqdmExt(std_tqdm):
    
    def __init__(self, task_id, run_id, caller, *args, **kwargs):
        super(TqdmExt, self).__init__(*args, **kwargs)
        self.task_id = task_id
        self.run_id = run_id
        self.caller = caller
        
    def update(self, n=1):
        displayed = super(TqdmExt, self).update(n)
        sleep()
        if displayed:
            try:
                external_callback(self.task_id, self.run_id, self.caller, **self.format_dict)
            finally:
                pass
        return displayed
    
    def close(self):
        cleanup = super(TqdmExt, self).close
        try:
            external_callback(self.task_id, self.run_id, self.caller, **self.format_dict)
        finally:
            cleanup()

class MessageAnnouncer:

    def __init__(self):
        self.listeners = dict()

    def listen(self, task_id):
        if task_id not in self.listeners.keys():
            q = queue.Queue(maxsize=1000000)
            self.listeners[task_id] = q
        return self.listeners[task_id]
    
    def disconnect(self, task_id):
        if task_id in self.listeners.keys():
            while not self.listeners[task_id].empty():
                msg = self.listeners[task_id].get()
                msg.task_done()
            del self.listeners[task_id]

    def announce(self, msg, task_id):
        #try:
            if task_id in self.listeners.keys():
                self.listeners[task_id].put_nowait(msg)
        #except queue.Full:
        #    del self.listeners[session_id][run_id]

announcer = MessageAnnouncer()
                
class InputFileSelection:
    pass

class EccTestbenchService:
    
    def __init__(self, root_folder: str, run_repository: RunRepository, socketio: SocketIO = None):
        self.logger = logging.getLogger(__name__)
        self.root_folder = root_folder
        self.run_repository = run_repository
        self.socketio = socketio
    
    def prepare_run_directory(self, selected_audio_files: list, root_folder: str, run_root_folder: str):
        if not os.path.exists(run_root_folder):
            os.mkdir(run_root_folder)
        for audio_file in selected_audio_files:
            file_basename = os.path.basename(audio_file)
            source_file_path = os.path.join(root_folder, file_basename)
            target_file_path = os.path.join(run_root_folder, file_basename)
            shutil.copyfile(src=source_file_path, dst=target_file_path)
    
    def build_testbench_from_run(self, run: Run, user, task_id:str = None) -> PLCTestbench:
        get_worker = lambda x: (globals()[x[0]], x[1])
        
        #path_manager = PathManager(run.root_folder)
        #database_manager = DatabaseManager(db_host, db_port, db_username, db_password)
        #user = { "email" : run.creator }
        #data_manager = DataManager(path_manager, database_manager, user, progress_monitor=__async_func__)

        packet_loss_simulators = list(map(get_worker, run.packet_loss_simulators))
        plc_algorithms = list(map(get_worker, run.plc_algorithms))
        output_analysers = list(map(get_worker, run.output_analysers))
        '''
        testbench = PLCTestbench(
                                 packet_loss_simulators,
                                 plc_algorithms,
                                 output_analysers,
                                 data_manager,
                                 path_manager,
                                 run.run_id
                                 )
        '''
        testbench_settings = {
            'root_folder': run.root_folder,
            'db_ip': db_host,
            'db_port': db_port,
            'db_username': db_username,
            'db_password': db_password,
            'progress_monitor': __async_func__(task_id, str(run.run_id)) if task_id else None
        }
        testbench = PLCTestbench(
                                packet_loss_simulators,
                                plc_algorithms,
                                output_analysers,
                                testbench_settings,
                                user.__dict__,
                                run.run_id
                                 )
        '''
        original_audio_tracks_ids = map(lambda x: { x[0]: x[1] }, run.original_audio_tracks)
        original_audio_tracks_ids_map = functools.reduce(lambda x, y: dict(list(x.items()) + list(y.items())),
                                                     original_audio_tracks_ids, dict())
        for original_audio_track_node in testbench.data_manager.get_data_trees():
            file_basename = os.path.basename(original_audio_track_node.file.path)
            original_audio_track_node.uuid = original_audio_tracks_ids_map[file_basename]
        '''
        return testbench
    
    def create_run(self, json_dict, run_id, user) -> PLCTestbench:

        configuration_map = {
            InputFileSelection: None,
            #GlobalSettings: [],
            PacketLossSimulator: [],
            PLCAlgorithm: [],
            OutputAnalyser: []
        }
        
        def copy_attributes(settings, json_dict):
            for setting in json_dict["settings"]:
                try:
                    conversion_function = globals()['__builtins__'][setting["type"]]
                    if (conversion_function != None):
                        setattr(settings, setting["property"], conversion_function(setting["value"]))
                except:
                    self.logger.info("Could not set property %s of type %s on Settings", setting["property"], setting["type"])
        
        def parse_configuration(configuration_map, json_dict) -> dict: 
            worker_name = json_dict["name"].replace(" ", "")
            worker_constructor =  globals()[worker_name] if worker_name in globals() else None
            worker_settings_name = worker_name + "Settings" if not worker_name.endswith("Settings") else worker_name
            worker_settings_constructor = globals()[worker_settings_name] if worker_settings_name in globals() else None
            worker_settings = worker_settings_constructor() if worker_settings_constructor != None else json_dict["settings"]
            worker_base = worker_constructor.__base__ if worker_constructor != None \
                                                         and worker_constructor.__base__ != object \
                                                         and worker_constructor.__base__ != Settings \
                                                      else None
            worker_key = worker_base if worker_base != None else worker_constructor
            worker_id = str(uuid.uuid4())
            
            if worker_settings_constructor != None:
                copy_attributes(worker_settings, json_dict)
            if isinstance(configuration_map[worker_key], list):
                configuration_map[worker_key].extend([(worker_constructor, worker_settings, worker_id) if worker_settings_constructor != None and worker_constructor != worker_settings.__class__ else worker_settings])
            else:
                configuration_map[worker_key] = worker_settings
            return configuration_map
        
        configuration_map = functools.reduce(parse_configuration, json_dict, configuration_map)
        
        #for global_settings in configuration_map[GlobalSettings]:
        #    global_settings.__progress_monitor__ = __async_func__
        
        #run_root_folder = os.path.join(self.root_folder, run_id)
        #self.prepare_run_directory(configuration_map[InputFileSelection], self.root_folder, run_root_folder)
        
        run = Run( #run_id=run_id,
                   #root_folder=run_root_folder,
                   root_folder=self.root_folder,
                   selected_input_files=configuration_map[InputFileSelection],
                   packet_loss_simulators=configuration_map[PacketLossSimulator],
                   plc_algorithms=configuration_map[PLCAlgorithm],
                   output_analysers=configuration_map[OutputAnalyser])
        
        testbench = self.build_testbench_from_run(run, user)
        run.run_id = testbench.run_id
        
        return run
    
    def save_run(self, run: Run, user):
        self.logger.info("Saving run %s", run.run_id)
        self.run_repository.update(run, user)
        
    def load_run(self, run_id, user) -> Run:
        self.logger.info("Loading run %s", run_id)
        run = self.run_repository.find_by_id(run_id, user)
        return run
    
    def launch_run_execution(self, run_id, user, task_id) -> PLCTestbench:
        self.logger.info("Task %s, executing run %s", task_id, run_id)
        run = self.load_run(run_id, user)
        #run.__ecctestbench__.global_settings_list[0].__progress_monitor__ = __async_func__
        #plc_testbench = run.__ecctestbench__
        
        plc_testbench = self.build_testbench_from_run(run, user, task_id)
        
        task = self.socketio.start_background_task(execute_elaboration, plc_testbench, user, self.on_run_completed(task_id))
        '''
        thread_0 = Thread(target=execute_elaboration,
                          args=[run.__ecctestbench__, self.on_run_completed])
        thread_0.daemon = True
        thread_0.start()
        '''
        execution_id = run_id
        self.logger.info("Run %s: execution %s launched", run_id, execution_id)
        return execution_id
    
    def on_run_completed(self, task_id):
        return lambda run_id, user: partial(__notifyRunCompletion__, task_id)(run_id, user)


def __notifyRunCompletion__(task_id, run_id, user):
    msg = __format_sse__(data=json.dumps({
                            "task_id": task_id,
                            "run_id": run_id,
                            "total": 100,
                            "nodeid" : str(run_id),
                            "nodetype" : "RunExecution",
                            "elapsed" : 0,
                            "currentPercentage": 100,
                            "eta": 0,
                            "timestamp": str(datetime.now()),
                            "progress": progress_cache[str(run_id)]
                        }, indent = 4).replace('\n', ' '),
                        event="run_execution")
    for idx in range(1, 10):
        announcer.announce(msg=msg, task_id=task_id)
        #print("msg:%s" % (msg))
        sleep(0.1)

def get_execution_last_event(last_event_id, user):
    return progress_cache[last_event_id] if last_event_id in progress_cache.keys() else None
        
def update_progress_cache(run_id, node_type, node_id, progress, caller) -> dict:
    if not run_id in progress_cache.keys():
        progress_cache[run_id] = dict()
    current_state = progress_cache[run_id]
    if node_id in current_state.keys() and current_state[node_id] == progress:
        return current_state
    current_state["revision"] = current_state["revision"] + 1 \
        if "revision" in current_state.keys() else 1
    current_state[node_id] = progress
    if node_type == PLCTestbench.__name__:
        current_state["run_id"] = node_id
        files = caller.data_manager.get_data_trees()
        current_file_index = min(len(files) - 1, current_state["current_root_index"] + 1 if "current_root_index" in current_state.keys() else 0)
        current_file = files[current_file_index]
        current_state["current_file"] = os.path.basename(current_file.file.path)
    if node_type == OriginalTrackWorker.__name__ \
            and (not "current_root" in current_state.keys() \
                or node_id != current_state["current_root"]):
        current_state["current_root"] = node_id
        current_state["current_root_index"] = current_state["current_root_index"] + 1 \
            if "current_root_index" in current_state.keys() else 0

    return current_state

def clean_progress_cache(run_id:str, user:User):
    del progress_cache[run_id]
    
def __async_func__(task_id:str = None, run_id:str = None):
    progressLoggerMethod = "TqdmExt"
    tid = task_id if task_id else str(uuid.uuid4())
    rid = run_id if run_id else str(uuid.uuid4())
    progressLogger = lambda caller: partial(globals()[progressLoggerMethod], tid, rid, caller) if progressLoggerMethod in globals().keys() else std_tqdm
    return progressLogger

def external_callback(task_id:str, run_id:str, caller, *args, **kwargs):
    caller_class_name = caller.__class__.__name__
    #print("caller_class_name=%s, args=%s, kwargs=%s" % (caller_class_name, args, kwargs))
    nodeid = str(caller.uuid) if hasattr(caller, "uuid") else str(caller.run_id) if hasattr(caller, "run_id") else ""
    currentPercentage = math.floor(kwargs["n"] / kwargs["total"] * 100)
    eta = math.ceil((kwargs["total"] - kwargs["elapsed"]) * (1 / (kwargs["rate"] if kwargs["rate"] != None else float('inf'))))
    
    progress_state = get_execution_last_event(run_id, User(id_="", email="", name=""))
    revision = progress_state["revision"] if progress_state and "revision" in progress_state.keys() else 0
    progress_state = update_progress_cache(run_id, caller_class_name, nodeid, currentPercentage, caller)
    new_revision = progress_state["revision"]
    
    if revision != new_revision:    
        data = json.dumps({
            "task_id": task_id,
            "run_id": run_id,
            "total": kwargs["total"],
            "nodeid" : nodeid,
            "nodetype" : caller_class_name,
            "elapsed" : kwargs["elapsed"],
            "currentPercentage": currentPercentage,
            "eta": eta,
            "timestamp": str(datetime.now()),
            "progress": progress_cache[run_id]
        }, indent=4).replace('\n', ' ')
        msg = __format_sse__(data=data,
            event="run_execution")
        #print("msg:%s" % (msg))
        announcer.announce(msg, task_id)

def __format_sse__(data: str, event=None) -> str:
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg

def execute_elaboration(ecctestbench, user, callback):
    ecctestbench.run()
    run_id = ecctestbench.run_id
    callback(run_id, user)
    sleep(3)
    clean_progress_cache(str(run_id), user)
