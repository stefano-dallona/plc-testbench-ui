from numpy import ndarray
import numpy as np
from pathlib import Path
import soundfile as sf

from plctestbench.file_wrapper import FileWrapper, DataFile, AudioFile as DefaultAudioFile, DEFAULT_DTYPE
from plctestbench.node import Node
from plctestbench.data_manager import DataManager
from plctestbench.plc_testbench import PLCTestbench as DefaultPLCTestbench

from ..repositories.mongodb.node_repository import NodeRepository
from ..models.user import User

def load_audio_file(audio_file: DefaultAudioFile,
                    offset: int,
                    numsamples: int,
                    sample_type: str = DEFAULT_DTYPE) -> ndarray:
    #offset = 0
    #numsamples = -1
    with sf.SoundFile(audio_file.path, 'r') as file:
        file.seek(min(int(offset if offset else 0), file.frames - 1))
        setattr(audio_file, "frames", file.frames)
        audio_file.data = file.read(frames=numsamples if numsamples else -1, dtype=sample_type)
        audio_file.path = file.name
        audio_file.samplerate = file.samplerate
        audio_file.channels = file.channels
        audio_file.subtype = file.subtype
        audio_file.endian = file.endian
        audio_file.audio_format = file.format

class AudioFile(DefaultAudioFile):
    def __init__(self, data: ndarray=None,
                    path: str=None,
                    samplerate: float=None,
                    channels: int=None,
                    subtype: str=None,
                    endian: str=None,
                    audio_format: str=None,
                    persist=True) -> None:

        self.samplerate = samplerate
        self.channels = channels
        self.subtype = subtype
        self.endian = endian
        self.audio_format = audio_format
        self.data = []
        self.path = path
        self.persist = False

        if self.path is None:
            raise ValueError('path must be specified')
        
    @classmethod
    def from_path(cls, path: str) -> FileWrapper:
        if not Path(path).exists():
            return None

        if path.split('.')[-1] == 'wav':
            file = AudioFile(path=path)
        else:
            file = DataFile(path=path)
        return file

class OriginalTrackNode(Node):
    def __init__(self, file=None, worker=None, settings=None, absolute_path=None, parent=None, database=None, folder_name=None) -> None:
        super().__init__(file=file, worker=worker, settings=settings, absolute_path=absolute_path, parent=parent, database=database, folder_name=folder_name)
        self.file = AudioFile(path=self.absolute_path + '.wav')
        load_audio_file(self.file, 0, 0)
        self.settings.add('fs', self.file.get_samplerate())
        
    def get_data(self) -> np.ndarray:
        return self.file.get_data()

    def get_track_name(self) -> str:
        return self.absolute_path.rpartition("/")[2].split(".")[0]

    def _run(self) -> None:
        print(self.get_track_name())
        self.get_worker().run()

class PLCTestbench(DefaultPLCTestbench):
    def __init__(self, original_audio_tracks: list = None,
                 packet_loss_simulators: list = None,
                 plc_algorithms: list = None,
                 output_analysers: list = None,
                 testbench_settings: dict = None,
                 user: dict = None,
                 run_id: int = None):
        if testbench_settings is None:
            raise ValueError("testbench_settings must be provided")
        self.data_manager = DataManager(testbench_settings, user)
        self.data_manager.node_classes[0] = OriginalTrackNode

        if run_id:
            self.data_manager.load_workers_from_database(run_id)
        elif packet_loss_simulators is None \
             or plc_algorithms is None \
             or output_analysers is None:
            raise ValueError("packet_loss_simulators, \
                              plc_algorithms and output_analysers \
                              must be provided if no run_id is provided")
        else:
            self.data_manager.set_workers(original_audio_tracks,
                                          packet_loss_simulators,
                                          plc_algorithms,
                                          output_analysers)

        calculated_run_id = self.data_manager.initialize_tree()
        #run = self.data_manager.database_manager.get_run(run_id)
        #node_data_map = self.retrieve_node_data(run['nodes'], user)
        #self.recursively_update_file_hash(node_data_map, self.data_manager.get_data_trees())
            
        self.run_id = run_id if run_id else calculated_run_id
        
    def retrieve_node_data(self, node_ids: str, user):
        node_repository = NodeRepository()
        user = User(id_=user["id_"], email=user["email"], name=user["name"])
        nodes = { node_repository.find_by_id(node_id, user) for node_id in node_ids }
        return nodes
    
    def recursively_update_file_hash(self, node_data_map: dict, node: Node):
        if node.get_id() in node_data_map.keys():
            node.file.hash = node_data_map[node].file_hash
        for child_node in node.children:
            self.recursively_update_file_hash(node_data_map, child_node)