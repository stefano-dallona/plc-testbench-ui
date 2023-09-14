from numpy import ndarray
import numpy as np
from pathlib import Path

from plctestbench.file_wrapper import FileWrapper, DataFile, AudioFile as DefaultAudioFile
from plctestbench.node import Node
from plctestbench.data_manager import DataManager
from plctestbench.plc_testbench import PLCTestbench as DefaultPLCTestbench

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

        self.run_id = self.data_manager.initialize_tree()