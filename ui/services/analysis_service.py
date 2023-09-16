
import logging
import os
import itertools
import pickle
import math

from ..models.samples import *
from ..models.user import *
from .plctestbench_service import EccTestbenchService
from ..services.configuration_service import ConfigurationService
from ..testbench.customization import OriginalTrackNode as CustomOriginalTrackNode

from plctestbench.node import *
from plctestbench.plc_testbench import *
from anytree import *

class AnalysisService:
    
    _logger = logging.getLogger(__name__)
    
    def __init__(self, ecctestbench_service: EccTestbenchService):
        self.ecctestbench_service = ecctestbench_service
    
    def find_audio_file(self,
                        run_id: str,
                        audio_file_node_id: str,
                        user,
                        plc_testbench: PLCTestbench = None,
                        offset: int = None,
                        numsamples: int = None,
                        sample_type: str = 'float32') -> AudioFile:
        run = self.ecctestbench_service.load_run(run_id, user)
        if run == None:
            return None
        
        self._logger.info(f"Loaded ecctestbench for {run_id} ...")
        
        plc_testbench = self.ecctestbench_service.build_testbench_from_run(run, user, readonly=True) if not plc_testbench else plc_testbench
        nodes_to_load = [ audio_file_node_id ]
        self.ecctestbench_service.load_files(plc_testbench, nodes_to_load, offset, numsamples, sample_type)
        
        for file_tree in plc_testbench.data_manager.get_data_trees():
            audio_file = self.__find_audio_file_by_node_id__(file_tree, audio_file_node_id)
            if audio_file != None:
                return audio_file.file, plc_testbench

        return None, plc_testbench
    
    def find_lost_samples(self,
                          run_id: str,
                          original_file_node_id: str,
                          loss_simulation_node_id: str,
                          unit_of_meas: str = "samples",
                          user = None) -> LostSamples:
        run = self.ecctestbench_service.load_run(run_id, user)
        if run == None:
            return None
        self._logger.info(f"Loaded ecctestbench for {run_id} ...")
        
        plc_testbench = self.ecctestbench_service.build_testbench_from_run(run, user, readonly=True)
        nodes_to_load = [ original_file_node_id, loss_simulation_node_id ]
        self.ecctestbench_service.load_files(plc_testbench, nodes_to_load)
        
        file_tree = self.__find_file_tree_by_node_id__(plc_testbench, original_file_node_id)
        original_audio_file = file_tree.file
        self._logger.info(f"file_tree:  {file_tree} ...")
        
        lost_samples_file = self.__find_lost_simulation_file_by_node_id__(file_tree, loss_simulation_node_id)
        self._logger.info(f"lost_samples_files:  {lost_samples_file} ...")
        
        sample_rate = 1 if unit_of_meas == "samples" else original_audio_file.samplerate
        lost_samples = self.__convertToLossIntervals__(len(original_audio_file.data), lost_samples_file.file.data, sample_rate)
        return lost_samples

    def get_audio_file_samples(self,
                        run_id: str,
                        audio_file_node_id: str,
                        channel: int = 0,
                        offset = None,
                        num_samples = None,
                        unit_of_meas = "samples",
                        user: User = None,
                        plc_testbench: PLCTestbench = None):
        audio_file, plc_testbench = self.find_audio_file(run_id, audio_file_node_id, user, plc_testbench, offset, num_samples)
        self._logger.info(f"Loaded audio file with path {audio_file.path} ...")
        samples = AudioFileSamples(node_id=audio_file_node_id, channel=channel, samples=audio_file.get_data(),
                                   offset=None, num_samples=None,
                                   sample_rate=1 if unit_of_meas=="samples" else audio_file.samplerate)
        return samples, plc_testbench
    
    def get_audio_file_waveform(self,
                            run_id: str,
                            audio_file_node_id: str,
                            max_slices: int,
                            user: User,
                            plc_testbench: PLCTestbench = None,
                            offset: int = 0,
                            num_samples: int = -1):
            audio_file, plc_testbench = self.find_audio_file(run_id, audio_file_node_id, user, plc_testbench, offset, num_samples)
            self._logger.info(f"Loaded audio file with path {audio_file.path} ...")
            waveform = DownsampledAudioFile(audio_file, max_slices)
            return waveform, plc_testbench
    
    def get_metric_samples(self,
                        run_id: str,
                        audio_file_node_id: str,
                        metric_node_id: str,
                        channel: int = 0,
                        offset = None,
                        num_samples = None,
                        unit_of_meas = "samples",
                        category = None,
                        user = None):
        run = self.ecctestbench_service.load_run(run_id, user)
        if run == None:
            return None
        self._logger.info(f"Loaded ecctestbench for {run_id} ...")
        
        plc_testbench = self.ecctestbench_service.build_testbench_from_run(run, user, readonly=True)
        nodes_to_load = [ audio_file_node_id, metric_node_id ]
        self.ecctestbench_service.load_files(plc_testbench, nodes_to_load)
        
        audio_file = self.__find_node_by_id__(plc_testbench, audio_file_node_id)
        if audio_file == None:
            return None
        total_audio_file_samples = len(audio_file.file.get_data())
        
        metric_file = self.__find_metric_file_by_node_id__(audio_file, metric_node_id, category)
        if metric_file == None:
            return None
        
        metric_samples = metric_file.get_data()
        category = "linear" if hasattr(metric_file.get_data(), '__iter__') else "scalar"
        metric_samples_num = num_samples
        if category == "scalar":
            metric_samples_num = 1
        elif num_samples == None:
            metric_samples_num = len(metric_samples)
        
        scale_position = unit_of_meas != "samples"
        samples = MetricSamples(node_id=metric_node_id,
                                samples=metric_samples,
                                total_original_file_samples=total_audio_file_samples,
                                offset=offset,
                                num_samples=metric_samples_num,
                                scale_position=scale_position,
                                category=category)
        return samples
    
    @staticmethod
    def __get_first__(data: list):
        return data[0] if len(data) > 0 else None
    
    @staticmethod
    def __find_node_by_id__(ecctestbench: PLCTestbench, node_id: str) -> Node:
        search = lambda x : str(x.get_id()) == node_id
        result = list(map(lambda tree: AnalysisService.__find_nodes_in_file_tree__(tree, search), ecctestbench.data_manager.get_data_trees()))
        result = list(itertools.chain(*result))
        return AnalysisService.__get_first__(result)
        
    @staticmethod
    def __find_nodes_in_file_tree__(file_tree: Node, predicate) -> Node:
        nodes = list(findall(node=file_tree, filter_=predicate))
        return nodes
    
    @staticmethod
    def __find_file_tree_by_node_id__(ecctestbench: PLCTestbench, node_id: str) -> Node:
        search = lambda x : (isinstance(x, OriginalTrackNode) or isinstance(x, CustomOriginalTrackNode)) and str(x.get_id()) == node_id #and x.uuid == node_id
        files_trees = list(filter(search, ecctestbench.data_manager.get_data_trees()))
        return AnalysisService.__get_first__(files_trees)
    
    @staticmethod
    def __find_lost_simulation_file_by_node_id__(file_tree: Node, node_id: str) -> Node:
        search = lambda x: isinstance(x, LostSamplesMaskNode) and str(x.get_id()) == node_id #and x.uuid == node_id
        return AnalysisService.__get_first__(AnalysisService.__find_nodes_in_file_tree__(file_tree, search))
    
    @staticmethod
    def __find_audio_file_by_node_id__(file_tree: Node, node_id: str) -> Node:
        search = lambda x: any(isinstance(x, n) for n in [OriginalTrackNode, ReconstructedTrackNode, CustomOriginalTrackNode]) and str(x.get_id()) == node_id #and x.uuid == node_id
        return AnalysisService.__get_first__(AnalysisService.__find_nodes_in_file_tree__(file_tree, search))
    
    @staticmethod
    def __find_audio_files__(file_tree: Node) -> list:
        search = lambda x: any(isinstance(x, n) for n in [OriginalTrackNode, ReconstructedTrackNode, CustomOriginalTrackNode])
        return AnalysisService.__find_nodes_in_file_tree__(file_tree, search)
    
    @staticmethod
    def __find_metric_file_by_node_id__(file_tree: Node, node_id: str, category = None) -> Node:
        #search = lambda x: isinstance(x, OutputAnalysisNode) and x.uuid == node_id \
        search = lambda x: isinstance(x, OutputAnalysisNode) and str(x.get_id()) == node_id \
            and (category == None or category == ConfigurationService.get_output_analyser_category(x.worker))
        return AnalysisService.__get_first__(AnalysisService.__find_nodes_in_file_tree__(file_tree, search))
    
    @staticmethod
    def __convertToLossIntervals__(num_samples, lost_samples, sample_rate) -> LostSamples:
        deltalist = [(e, i - e) for i, e in enumerate(lost_samples)]
        key_func = lambda x: x[1]
        groupedlist = [list(g) for _, g in itertools.groupby(deltalist, key_func)]
        counterlist = [(l[0][0], len(l)) for l in groupedlist]
        data = [LostInterval(int(x), int(w), sample_rate) for x, w in counterlist]
        duration = float(num_samples / sample_rate)
        return LostSamples(duration, data)