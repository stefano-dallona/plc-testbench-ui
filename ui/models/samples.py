
from flask import json
from typing import List

import numpy as np

from .base_model import *

class LostInterval(Serializable):
    
    def __init__(self, start_sample, num_samples, sample_rate = 1):
        self.__sample_rate__ = sample_rate
        self.start_sample = start_sample
        self.num_samples = num_samples
        self.x = float(self.start_sample / self.__sample_rate__)
        self.w = float(self.num_samples / self.__sample_rate__)

class LostSamples(Serializable):

    def __init__(self, num_intervals, lost_intervals: List[LostInterval]):
        self.num_intervals = num_intervals
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
        normalized_channel_samples = (channel_samples-np.min(channel_samples))/(np.max(channel_samples)-np.min(channel_samples))
        position = lambda i : i if sample_rate == 1 else float(i/sample_rate)
        start_sample = offset if offset != None else 0
        start_sample = max(start_sample, 0)
        end_sample = offset + num_samples if offset != None and num_samples != None else len(samples)
        end_sample = min(end_sample, len(samples))
        end_sample = end_sample if end_sample >= start_sample else start_sample
        normalized_samples = [{"cx": position(start_sample + i), "cy":y} for i,y in enumerate(normalized_channel_samples[start_sample:end_sample])]
        return normalized_samples

class MetricSamples(Serializable):

    def __init__(self, node_id: int, samples, total_original_file_samples: int, 
                 offset: int, num_samples: int, scale_position: bool = False):
        self.node_id = node_id
        self.total_samples = len(samples)
        self.total_original_file_samples = total_original_file_samples if scale_position and total_original_file_samples != None else self.total_samples
        self.offset = offset
        self.num_samples = num_samples
        self.data = self.__filter_data__(list(samples), offset, num_samples, float(self.total_original_file_samples / self.total_samples))
    
    @staticmethod
    def __filter_data__(samples, offset: int, num_samples: int, sample_rate: int):
        position = lambda i : i if sample_rate == 1 else float(i/sample_rate)
        start_sample = offset if offset != None else 0
        start_sample = max(start_sample, 0)
        end_sample = offset + num_samples if offset != None and num_samples != None else len(samples)
        end_sample = min(end_sample, len(samples))
        end_sample = end_sample if end_sample >= start_sample else start_sample
        filtered_samples = [{"sample": position(start_sample + i), "values": y.tolist()} for i,y in enumerate(samples[start_sample:end_sample])]
        return filtered_samples

        