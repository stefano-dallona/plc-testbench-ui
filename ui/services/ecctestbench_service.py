from plctestbench.plc_testbench import *
from plctestbench.settings import *
from plctestbench.loss_simulator import *
from plctestbench.plc_algorithm import *
from plctestbench.output_analyser import *
from plctestbench.data_manager import *
from plctestbench.path_manager import *
from plctestbench.node import *
from plctestbench.file_wrapper import *

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

from ..repositories.run_repository import *
from ..config.app_config import Config
from ..models.run import *

class TqdmExt(std_tqdm):
    
    def __init__(self, caller, *args, **kwargs):
        super(TqdmExt, self).__init__(*args, **kwargs)
        self.caller = caller
        
    def update(self, n=1):
        displayed = super(TqdmExt, self).update(n)
        sleep()
        if displayed:
            external_callback(self.caller, **self.format_dict)
        return displayed

class MessageAnnouncer:

    def __init__(self):
        self.listeners = []

    def listen(self):
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

announcer = MessageAnnouncer()
                
class InputFileSelection:
    pass

class EccTestbenchService:
    
    def __init__(self, root_folder: str, run_repository: RunRepository, socketio: SocketIO = None):
        self.logger = logging.getLogger(__name__)
        self.root_folder = root_folder
        self.run_repository = run_repository
        self.socketio = socketio
    
    def save_run(self, run: Run):
        self.logger.info("Saving run %s", run.run_id)
        self.run_repository.add(run)
        
    def load_run(self, run_id) -> Run:
        self.logger.info("Loading run %s", run_id)
        return self.run_repository.get(run_id)
    
    def launch_run_execution(self, run_id) -> PLCTestbench:
        self.logger.info("Executing run %s", run_id)
        run = self.load_run(run_id)
        run.__ecctestbench__.global_settings_list[0].__progress_monitor__ = __async_func__
        
        task = self.socketio.start_background_task(execute_elaboration, run.__ecctestbench__, self.on_run_completed)
        '''
        thread_0 = Thread(target=execute_elaboration,
                          args=[run.__ecctestbench__, self.on_run_completed])
        thread_0.daemon = True
        thread_0.start()
        '''
        execution_id = run_id
        self.logger.info("Run %s: execution %s launched", run_id, execution_id)
        return execution_id
    
    def on_run_completed(self, run_id):
        run = self.load_run(run_id)
        run.status = RunStatus.COMPLETED
        self.save_run(run)
        __notifyRunCompletion__(run_id)
    
    def prepare_run_directory(self, selected_audio_files: list, root_folder: str, run_root_folder: str):
        if not os.path.exists(run_root_folder):
            os.mkdir(run_root_folder)
        for audio_file in selected_audio_files:
            file_basename = os.path.basename(audio_file)
            source_file_path = os.path.join(root_folder, file_basename)
            target_file_path = os.path.join(run_root_folder, file_basename)
            shutil.copyfile(src=source_file_path, dst=target_file_path)
    
    def create_run(self, json_dict, run_id) -> PLCTestbench:

        configuration_map = {
            InputFileSelection: None,
            GlobalSettings: [],
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
            
            if worker_settings_constructor != None:
                copy_attributes(worker_settings, json_dict)
            if isinstance(configuration_map[worker_key], list):
                configuration_map[worker_key].extend([(worker_constructor, worker_settings) if worker_settings_constructor != None and worker_constructor != worker_settings.__class__ else worker_settings])
            else:
                configuration_map[worker_key] = worker_settings
            return configuration_map
        
        configuration_map = functools.reduce(parse_configuration, json_dict, configuration_map)
        
        for global_settings in configuration_map[GlobalSettings]:
            global_settings.__progress_monitor__ = __async_func__
        
        run_root_folder = os.path.join(self.root_folder, run_id)
        self.prepare_run_directory(configuration_map[InputFileSelection], self.root_folder, run_root_folder)
        
        path_manager = PathManager(run_root_folder)
        data_manager = DataManager(path_manager)

        testbench = PLCTestbench(configuration_map[PacketLossSimulator],
                                 configuration_map[PLCAlgorithm],
                                 configuration_map[OutputAnalyser],
                                 configuration_map[GlobalSettings], data_manager, path_manager, run_id)
        
        return Run(testbench, configuration_map[InputFileSelection])

def __notifyRunCompletion__(run_id):
    #sleep(1)
    msg = __format_sse__(data=json.dumps({ "total": 100, "nodeid" : run_id, "nodetype" : "RunExecution", "elapsed" : "", "currentPercentage": 100, "eta": 0, "timestamp": str(datetime.now()) }, indent = 4).replace('\n', ' '), event="run_execution")
    print("msg:%s" % (msg))
    announcer.announce(msg=msg)
    
def __async_func__(self):
    progressLoggerMethod = "TqdmExt" 
    progressLogger = partial(globals()[progressLoggerMethod], self) if progressLoggerMethod in globals().keys() else std_tqdm
    return progressLogger

def external_callback(caller, *args, **kwargs):
    caller_class_name = caller.__class__.__name__
    print("caller_class_name=%s, args=%s, kwargs=%s" % (caller_class_name, args, kwargs))
    nodeid = caller.uuid if hasattr(caller, "uuid") else ""
    print("nodeid=%s" % (nodeid))
    currentPercentage = math.floor(kwargs["n"] / kwargs["total"] * 100)
    eta = math.ceil((kwargs["total"] - kwargs["elapsed"]) * (1 / kwargs["rate"]))
    msg = __format_sse__(data=json.dumps({ "total": kwargs["total"], "nodeid" : nodeid, "nodetype" : caller_class_name, "elapsed" : kwargs["elapsed"], "currentPercentage": currentPercentage, "eta": eta, "timestamp": str(datetime.now()) }, indent = 4).replace('\n', ' '), event="run_execution")
    print("msg:%s" % (msg))
    announcer.announce(msg=msg)

def __format_sse__(data: str, event=None) -> str:
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg

def execute_elaboration(ecctestbench, callback):
    ecctestbench.run()
    run_id = ecctestbench.uuid
    callback(run_id)
