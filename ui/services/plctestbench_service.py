from plctestbench.plc_testbench import *
from plctestbench.settings import *
from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.data_manager import *
from plctestbench.path_manager import *
from plctestbench.node import *
from plctestbench.file_wrapper import *
from plctestbench.worker import *
import plctestbench.utils as plctestbenchutils

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
from numpy import ndarray

from ..repositories.pickle.run_repository import RunRepository
from ..config.app_config import *
from ..models.run import *
from ..models.user import *
from ..services.configuration_service import *

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
    
    def get_testbench_settings(self, run: Run, config: Config, task_id: str = None) -> dict:
        testbench_settings = {
            'root_folder': run.root_folder,
            'db_conn_string': config.db_conn_string,
            'db_ip': db_host,
            'db_port': db_port,
            'db_username': db_username,
            'db_password': db_password,
        #    'progress_monitor': __async_func__(task_id, str(run.run_id)) if task_id else None
        }
        return testbench_settings
    
    def build_testbench_from_run(self, run: Run, user, task_id: str = None) -> PLCTestbench:
        get_worker = lambda x: (globals()[x[0]], x[1])
        
        original_audio_tracks = list(map(lambda filename: (OriginalAudio, OriginalAudioSettings(filename)), run.selected_input_files))
        packet_loss_simulators = list(map(get_worker, run.packet_loss_simulators))
        plc_algorithms = list(map(get_worker, run.plc_algorithms))
        output_analysers = list(map(get_worker, run.output_analysers))

        testbench_settings = self.get_testbench_settings(run, config, task_id)
        testbench = PLCTestbench(
                                original_audio_tracks if not run.run_id else None,
                                packet_loss_simulators if not run.run_id else None,
                                plc_algorithms if not run.run_id else None,
                                output_analysers if not run.run_id else None,
                                testbench_settings,
                                user.__dict__,
                                run.run_id
                                )

        return testbench
    
    def load_files(self,
                   plc_testbench: PLCTestbench,
                   node_ids: list,
                   offset: int = None,
                   numsamples: int = None):
        nodes_to_load = []
        for root_node in plc_testbench.data_manager.root_nodes:
            for node in LevelOrderIter(root_node):
                if node.get_id() in node_ids:
                    nodes_to_load.append(node)
        
        def load_audio_file(audio_file: AudioFile,
                            offset: int = None,
                            numsamples: int = None) -> ndarray:
            offset = 0
            numsamples = -1
            with sf.SoundFile(audio_file.path, 'r') as file:
                file.seek(int(offset if offset else 0))
                audio_file.data = file.read(frames=numsamples if numsamples else -1, dtype=DEFAULT_DTYPE)
                audio_file.path = file.name
                audio_file.samplerate = file.samplerate
                audio_file.channels = file.channels
                audio_file.subtype = file.subtype
                audio_file.endian = file.endian
                audio_file.audio_format = file.format

        for node in nodes_to_load:
            node_class = node.__class__
            if node_class == OriginalTrackNode:
                node.file = AudioFile.from_path(node.absolute_path + '.wav')
                node.file.persist = False
                #node.file.load()
                load_audio_file(node.file, offset, numsamples)
            elif node_class == LostSamplesMaskNode:
                node.file = DataFile(path=node.absolute_path + '.npy', persist=False)
            elif node_class == ReconstructedTrackNode:
                node.file = AudioFile.from_path(node.absolute_path + '.wav')
                node.file.persist = False
                #node.file.load()
                load_audio_file(node.file, offset, numsamples)
            elif node_class == OutputAnalysisNode:
                node.file = DataFile(path=node.absolute_path + '.pickle', persist=False)

        return plc_testbench
    
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
                    value = conversion_function(setting["value"]) if (conversion_function != None) else setting["value"]
                    if (hasattr(settings, "settings") and type(settings.settings) is dict):
                        settings.settings[setting["property"]] = value
                    else:
                        setattr(settings, setting["property"], value)
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
            worker_base = ConfigurationService.get_worker_base_class(worker_constructor)
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
        
        run = Run(root_folder=self.root_folder,
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
        
        global progress_monitor
        progress_monitor = __async_func__(task_id, str(run.run_id))
        

        plctestbenchutils.progress_monitor = __async_func__(task_id, str(run.run_id))
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
    if node_type == OriginalAudio.__name__ \
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
    #nodeid = str(caller.uuid) if hasattr(caller, "uuid") else str(caller.run_id) if hasattr(caller, "run_id") else ""
    nodeid = str(caller.get_node_id()) if hasattr(caller, "get_node_id") else str(caller.run_id) if hasattr(caller, "run_id") else ""
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
    run_id = ecctestbench.run_id
    '''
    progress_cache[str(run_id)] = {"revision": 1,
                                   "run_id": str(run_id),
                                   "current_root_index": 0,
                                   "current_file": os.path.basename(ecctestbench.data_manager.get_data_trees()[0].file.path)}
    '''
    ecctestbench.run()
    callback(run_id, user)
    sleep(3)
    clean_progress_cache(str(run_id), user)
