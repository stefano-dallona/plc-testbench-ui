from flask import request, Blueprint, session
from flask_socketio import SocketIO, emit

import os
import math
from  base64 import b64encode
import wave
import gzip
import logging
import time
import uuid

from ..config.app_config import config
from ..services.analysis_service import AnalysisService
from ..services.ecctestbench_service import EccTestbenchService
from ..services.authentication_service import token_required, get_user_from_jwt_token
from ..repositories.pickle.run_repository import RunRepository
from ..repositories.mongodb.run_repository import RunRepository as MongoRunRepository

logging.getLogger('engineio').setLevel(level=logging.DEBUG)

streaming_api = Blueprint("streaming", __name__, url_prefix="/streaming")
run_repository = RunRepository(config.data_dir)
run_repository_mongodb2 = MongoRunRepository()
#ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository)
ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository_mongodb2)
analysis_service = AnalysisService(ecctestbench_service=ecctestbench_service)

ping_interval = 1
ping_timeout = 10 * ping_interval

socketio = SocketIO(cors_allowed_origins='*',
            #async_mode="threading", # apparently mutually exclusive with websocket mode
            async_mode="eventlet", # apparently mutually exclusive with websocket mode
            logger=True,
            engineio_logger=True,
            ping_timeout=ping_timeout,
            ping_interval=ping_interval,
            transports=[
                'websocket',
                #'polling',
            ])
clients = dict()
track_acks = dict()
active_streamings = dict()
max_nack_chunks = 0

def get_socketio() -> SocketIO:
    return socketio

def gen_header(sampleRate, bitsPerSample, channels, samples):
    datasize = samples * channels * bitsPerSample // 8
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

def stream_audio_file(socketio, event, namespace, file_path):
    def generate(file_path):
        with open(file_path, "rb") as af:
            data = af.read(1024)
            while data:
                yield data
                data = af.read(1024)
                
    def get_stats(file_path):
        f_stats = os.stat(file_path)
        return { att.replace("st_", ""):getattr(f_stats, att) for att in dir(f_stats) if att.startswith("st_") }
        
    first_response = True
    for data in generate(file_path):
        payload = dict()
        if first_response:
            first_response = False
            payload = { **payload, **get_stats(file_path) }
        payload = { **payload, **{ "data": b64encode(data) } }
        socketio.emit(event, payload)

@socketio.on('connect')
def on_connect():
    print("%s connected" % (request.sid))
    clients[request.sid] = request.sid
    
@socketio.on('disconnect')
def on_disconnect():
    print("%s disconnected" % (request.sid))
    del clients[request.sid]
    del track_acks[request.sid]
    
@socketio.on('track-ack')
def on_track_ack(message):
    chunk_num = message["chunk_num"]
    track_acks[request.sid] = chunk_num
    print("%s acknowledge received for chunk %d" % (request.sid, chunk_num))

@socketio.on('track-play')
def stream_track(message):
    run_id = message["run_id"]
    audio_file_node_id = message["audio_file_node_id"]
    original_file_node_id = message["original_file_node_id"]
    start_time = message["start_time"]
    stop_time = message["stop_time"]
    stream_id = str(uuid.uuid4())
    authorization_token = message["authorization"]
    user = get_user_from_jwt_token(authorization_token)
    
    audio_file = analysis_service.find_audio_file(run_id, audio_file_node_id, user)
    
    def send_file(sid, start_time, stop_time):
        
        def moderate_flow(sid, current_chunk_num):
            while(sid in track_acks.keys() and current_chunk_num - track_acks[sid] > max_nack_chunks):
                not_ack_chunks = current_chunk_num - track_acks[sid]
                print("current_chunk_num: %d, track_acks[%s]: %d, not_ack_chunks: %d" % (current_chunk_num, sid, track_acks[sid], not_ack_chunks))
                socketio.sleep(0)
    
        def generate_chunks(infile, start_time, stop_time):
            sr = infile.getframerate()
            tot_samples = infile.getnframes()
            start_sample = max(math.floor(start_time * sr), 0) if start_time != None else 0
            last_sample = min(math.floor(stop_time * sr), tot_samples) if stop_time != None else tot_samples
            current_sample = start_sample
            chunk_size = sr
            track_acks[sid] = 0
            chunk_num = 1
            while(current_sample < last_sample):
                infile.setpos(current_sample)
                num_samples = min(chunk_size, last_sample - current_sample)
                chunk = infile.readframes(nframes=num_samples)
                encoded_chunk = str(b64encode(chunk)).replace("b'", "").replace("'", "")
                last_chunk = current_sample + num_samples >= tot_samples
                yield encoded_chunk, sr, current_sample, current_sample + num_samples, last_chunk, chunk_num
                socketio.sleep(0)
                moderate_flow(sid, chunk_num)
                chunk_num += 1
                current_sample += num_samples
            
        with wave.open(audio_file.get_path(), 'rb') as infile:
            for chunk, sr, start_sample, last_sample, last_chunk, chunk_num in generate_chunks(infile, start_time, stop_time):
                if not sid in clients.keys() or not stream_id in active_streamings.keys():
                    socketio.emit('track-stream-stopped',  {}, room=sid)
                    socketio.sleep(0)
                    return
                
                socketio.emit('track-stream',  {
                    'stream_id': stream_id,
                    'chunk_num': chunk_num,
                    'sample_rate': sr,
                    'n_frames': infile.getnframes(),
                    'channels': infile.getnchannels(),
                    'bits_per_sample': infile.getsampwidth() * 8,
                    'last_chunk': last_chunk,
                    'chunk': chunk #gzip.compress(chunk, 5)
                }, room=sid)
                
                socketio.sleep(0)
                print("")
                print("chunk %s-%s sent" % (start_sample, last_sample))
    active_streamings[stream_id] = stream_id
    task = socketio.start_background_task(send_file, request.sid, start_time, stop_time)
    task.join()
    if stream_id in active_streamings.keys():
        del active_streamings[stream_id]
    
@socketio.on('track-stop')
def stop_track_streaming(message):
    stream_id = message["stream_id"]
    if stream_id in active_streamings.keys():
        del active_streamings[stream_id]
