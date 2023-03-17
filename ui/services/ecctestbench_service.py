from ecctestbench.ui.repositories.run_repository import *
from ecctestbench.ecc_testbench import *
from ecctestbench.settings import *
from ecctestbench.loss_simulator import *
from ecctestbench.ecc_algorithm import *
from ecctestbench.output_analyser import *
from ecctestbench.data_manager import *
from ecctestbench.path_manager import *
from ecctestbench.node import *
from ecctestbench.file_wrapper import *

import logging
from flask import json
from datetime import datetime
import uuid
from functools import partial
import math
import queue
from tqdm.auto import tqdm as std_tqdm

class TqdmExt(std_tqdm):
    
    def __init__(self, caller, *args, **kwargs):
        super(TqdmExt, self).__init__(*args, **kwargs)
        self.caller = caller
        
    def update(self, n=1):
        displayed = super(TqdmExt, self).update(n)
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

class EccTestbenchService:
    
    def __init__(self, run_repository: RunRepository):
        self.logger = logging.getLogger(__name__)
        self.run_repository = run_repository
    
    def saveRun(self, run: ECCTestbench):
        self.logger.info("Saving run %s", run.uuid)
        self.run_repository.add(run)
        
    def loadRun(self, run_id) -> ECCTestbench:
        self.logger.info("Loading run %s", run_id)
        return self.run_repository.get(run_id)
    
    def launchRunExecution(self, run_id) -> ECCTestbench:
        self.logger.info("Executing run %s", run_id)
        ecctestbench = self.loadRun(run_id)
        ecctestbench.settings.__progress_monitor__ = __async_func__
        execution_id = ecctestbench.run()
        __notifyRunCompletion__(run_id)
        # TODO - remove as soon as EccTestbench run method will return an execution id
        execution_id = str(uuid.uuid4)
        self.logger.info("Run %s: execution %s completed", run_id, execution_id)
        return execution_id
    
    def parseJsonIntoEccTestBench(self, jsonDict) -> ECCTestbench:
        settings = Settings()
        loss_simulators = []
        ecc_algorithms = []
        output_analysers = []
        for k, v in jsonDict.items():
            print("k:%s, v:%s" % (k, v))
            if hasattr(settings, k):
                attr_type = type(getattr(settings, k)).__name__
                attr_val = str(list(map(lambda x: "'" + x +  "'", v.split(",")))) if attr_type == "tuple" else "'" + v + "'"
                eval_str = "eval(\"" + attr_type + "(" + str(attr_val) + ")" + "\")"
                print("%s" % (eval_str))
                setattr(settings, k, eval(eval_str))
            if k == "eccAlgorithms":
                ecc_algorithms = [globals()[a] for a in v] if isinstance(v, list) else [globals()[v]]
            if k == "outputAnalysers":
                output_analysers = [globals()[a] for a in v] if isinstance(v, list) else [globals()[v]]
            if k.startswith("lossModel-"):
                prefix, index = k.split("lossModel-")
                lossModel = v
                lossSimulator = jsonDict["lossSimulator-" + index]
                print("lossModel:%s, index:%s, lossSimulator:%s" % (lossModel, index, lossSimulator))
                loss_simulators += [(globals()[lossSimulator], globals()[lossModel])]
        
        #loss_simulators = [(PacketLossSimulator, GilbertElliotLossModel), (PacketLossSimulator, BinomialLossModel)]
        #ecc_algorithms = [LowCostEcc, ZerosEcc]
        #output_analysers = [MSECalculator]
        settings.__progress_monitor__ = __async_func__
        
        print("settings:%s, loss_simulators:%s, ecc_algorithms:%s, output_analysers:%s" % (settings, loss_simulators, ecc_algorithms, output_analysers))
        path_manager = PathManager(jsonDict["inputFilesPath"])
        data_manager = DataManager(path_manager)

        testbench = ECCTestbench(loss_simulators, ecc_algorithms, output_analysers, settings, data_manager, path_manager)
        return testbench

def __notifyRunCompletion__(run_id):
    #sleep(1)
    msg = format_sse(data=json.dumps({ "total": 100, "nodeid" : run_id, "nodetype" : "RunExecution", "elapsed" : "", "currentPercentage": 100, "eta": 0, "timestamp": str(datetime.now()) }, indent = 4).replace('\n', ' '), event="run_execution")
    print("msg:%s" % (msg))
    announcer.announce(msg=msg)
    
def __async_func__(self):
    progressLoggerMethod = "TqdmExt" 
    progressLogger = partial(globals()[progressLoggerMethod], self) if progressLoggerMethod in globals().keys() else std_tqdm
    return progressLogger

def external_callback(caller, *args, **kwargs):
    caller_class_name = caller.__class__.__name__
    print("caller_class_name=%s, args=%s, kwargs=%s" % (caller_class_name, args, kwargs))
    isTestbench = isinstance(caller, ECCTestbench)
    isOriginalTrack = isinstance(caller, OriginalTrackWorker)
    isLossSimulator = isinstance(caller, PacketLossSimulator)
    isEccAlgorithm = isinstance(caller, ECCAlgorithm)
    isOutputAnalyzer = isinstance(caller, OutputAnalyser)
    nodeid = caller.uuid if isTestbench else \
             caller.uuid if isOriginalTrack else \
             caller.uuid if isLossSimulator else \
             caller.uuid if isEccAlgorithm else \
             caller.uuid if isOutputAnalyzer else \
             ""
    print("isTestbench=%s, isOriginalTrack=%s, isLossSimulator=%s, isEccAlgorithm=%s, isOutputAnalyzer=%s, nodeid=%s" % (isTestbench, isOriginalTrack, isLossSimulator, isEccAlgorithm, isOutputAnalyzer, nodeid))
    currentPercentage = math.floor(kwargs["n"] / kwargs["total"] * 100)
    eta = math.ceil((kwargs["total"] - kwargs["elapsed"]) * (1 / kwargs["rate"]))
    msg = format_sse(data=json.dumps({ "total": kwargs["total"], "nodeid" : nodeid, "nodetype" : caller_class_name, "elapsed" : kwargs["elapsed"], "currentPercentage": currentPercentage, "eta": eta, "timestamp": str(datetime.now()) }, indent = 4).replace('\n', ' '), event="run_execution")
    print("msg:%s" % (msg))
    announcer.announce(msg=msg)

def format_sse(data: str, event=None) -> str:
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg
    