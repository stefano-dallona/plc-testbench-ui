
from flask import json
from typing import List

import numpy as np
import math
import sys

from plctestbench.file_wrapper import AudioFile

from .base_model import *

minFloat = np.float32("1.0e-10")

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class LostInterval(Serializable):
    
    def __init__(self, start_sample, num_samples, sample_rate = 1):
        self.__sample_rate__ = sample_rate
        self.start_sample = start_sample
        self.num_samples = num_samples
        self.x = float(self.start_sample / self.__sample_rate__)
        self.width = float(self.num_samples / self.__sample_rate__)
        self.color = 'white'

class LostSamples(Serializable):

    def __init__(self, duration, lost_intervals: List[LostInterval]):
        self.duration = duration
        self.lost_intervals = lost_intervals

class AudioFileSamples(Serializable):
    
    def __init__(self, node_id: int, channel: int, samples: int, offset: int, num_samples: int, sample_rate = 1):
        self.node_id = node_id
        self.channel = channel
        self.offset = offset
        self.num_samples = num_samples
        self.sample_rate = sample_rate
        self.data = self.__filter_data__(samples, channel, offset, num_samples, sample_rate)
    
    @staticmethod
    def __filter_data__(samples, channel: int, offset: int, num_samples: int, sample_rate: int):
        channel_samples = samples[:, channel]
        position = lambda i : i if sample_rate == 1 else float(i/sample_rate)
        start_sample = offset if offset != None else 0
        start_sample = max(start_sample, 0)
        end_sample = offset + num_samples if offset != None and num_samples != None else len(samples)
        end_sample = min(end_sample, len(samples))
        end_sample = end_sample if end_sample >= start_sample else start_sample
        filtered_samples = [{"cx": position(start_sample + i), "cy":y} for i,y in enumerate(channel_samples[start_sample:end_sample])]
        return filtered_samples

class DownsampledAudioFile:
    
    def __init__(self, input_file: AudioFile, max_slices: int):
        self.input_file = input_file
        self.frames = input_file.frames if getattr(input_file, "frames") else len(input_file.data)
        self.num_samples = len(input_file.data)
        self.sample_rate = input_file.samplerate
        self.duration = self.frames * 1.0 / self.sample_rate
        self.max_slices = max_slices if max_slices > 0 else self.num_samples

    def load(self, channel, offset: int = None, n_samples: int = None):
        start_sample = 0 if offset == None else offset
        num_samples = len(self.input_file.get_data()) if n_samples == None else n_samples
        '''
        if self.max_slices == self.num_samples:
            start_sample = 0
            num_samples = self.num_samples
        '''
        base_data = self.input_file.get_data()[start_sample : start_sample + num_samples]
        channel_data = base_data[:, channel]
        data = np.where(channel_data == 0.0, minFloat, channel_data)
        
        samples_per_slice = num_samples / self.max_slices

        if len(data) <= self.max_slices:
            self.data = { str(start_sample + index) : str(value) for index, value in enumerate(data) }
            return
        
        slices_data = map(lambda i: data[math.floor(i * samples_per_slice) : math.floor((i + 1) * samples_per_slice)], range(0, self.max_slices))        

        result = {}
        for index, slice in enumerate(slices_data):
            slice_min = min(slice[:]) if len(slice) > 0 else 0
            slice_max = max(slice[:]) if len(slice) > 0 else 0
            result[str(start_sample + math.floor(index * samples_per_slice))] = str(slice_min)
            result[str(start_sample + math.floor(index * samples_per_slice) + 1)] = str(slice_max)
        
        self.data = result
    

class MetricSamples(Serializable):

    def __init__(self, node_id: int, samples, total_original_file_samples: int, 
                 offset: int, num_samples: int, scale_position: bool = False, category: str = "linear"):
        self.node_id = node_id
        self.category = category
        self.total_samples = 1
        if category == "linear":
            self.total_samples = len(samples)
        self.total_original_file_samples = total_original_file_samples if scale_position and total_original_file_samples != None else self.total_samples
        self.offset = offset
        self.num_samples = num_samples
        self.data = samples
        if category == "linear":
            self.data = self.__filter_data__(list(samples), offset, num_samples, float(self.total_original_file_samples / self.total_samples))
    
    @staticmethod
    def __filter_data__(samples, offset: int, num_samples: int, sample_rate: int):
        position = lambda i : i if sample_rate == 1 else float(i/sample_rate)
        start_sample = offset if offset else 0
        start_sample = max(start_sample, 0)
        end_sample = offset + num_samples if offset and num_samples and num_samples >= 0 else len(samples)
        end_sample = min(end_sample, len(samples))
        end_sample = end_sample if end_sample >= start_sample else start_sample
        filtered_samples = [{"sample": position(start_sample + i), "values": y.tolist()} for i,y in enumerate(samples[start_sample:end_sample])]
        return filtered_samples
