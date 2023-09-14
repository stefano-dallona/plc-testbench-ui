import functools
import soundfile as sf
import io
import itertools

from flask import Blueprint, json, request, make_response, send_file, session
from flask import current_app
from flask_api import status
from flask_login import login_required

from ..config.app_config import config
from ..repositories.pickle.run_repository import RunRepository
from ..repositories.mongodb.run_repository import RunRepository as MongoRunRepository
from ..services.analysis_service import AnalysisService
from ..services.plctestbench_service import EccTestbenchService
from ..models.base_model import *
from ..models.samples import *
from ..models.user import *

from .streaming_api import stream_audio_file as stream_file
from ..services.authentication_service import token_required


class DefaultJsonEncoder:
    @classmethod
    def to_json(cls, obj):
        return obj.__dict__ if hasattr(obj, '__dict__') else obj


run_repository = RunRepository(config.data_dir)

run_repository_mongodb2 = MongoRunRepository()

# ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository)
ecctestbench_service = EccTestbenchService(
    config.data_dir, run_repository=run_repository_mongodb2)
analysis_api = Blueprint("analysis", __name__, url_prefix="/analysis")
analysis_service = AnalysisService(ecctestbench_service=ecctestbench_service)


# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/loss-simulations/0b06e77f-2228-4b54-b78b-955602e32dc5
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/loss-simulations/<loss_simulation_node_id>', methods=['GET'])
# @login_required
@token_required
def find_lost_samples(run_id, original_file_node_id, loss_simulation_node_id, user):
    unit_of_meas = request.args.get('unit_of_meas')
    unit_of_meas = unit_of_meas if unit_of_meas != None else "samples"

    current_app.logger.info(
        f"Retrieving lost samples from run_id {run_id} and file {original_file_node_id} and loss simulation {loss_simulation_node_id}")
    lost_samples = analysis_service.find_lost_samples(
        run_id, original_file_node_id, loss_simulation_node_id, unit_of_meas, user)
    if lost_samples != None:
        return json.dumps(lost_samples, default=DefaultJsonEncoder.to_json), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND

# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7
# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0


@analysis_api.route("/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>")
# @login_required
#@token_required
def stream_audio_file(run_id, original_file_node_id, audio_file_node_id, user: User = None):
    if not user:
        user = User(id_="stefano.dallona@gmail.com", email="stefano.dallona@gmail.com", name="Stefano")
    offset = request.args.get("offset", type=int, default=0)
    num_samples = request.args.get("num_samples", type=int, default=-1)
    audio_file, plc_testbench = analysis_service.find_audio_file(
        run_id, audio_file_node_id, user, None, offset, num_samples)
    if audio_file != None:
        output = io.BytesIO()
        sf.write(output,
                 audio_file.data,
                 audio_file.samplerate,
                 audio_file.subtype,
                 audio_file.endian,
                 audio_file.audio_format)
        #return send_file(audio_file.path, mimetype='audio/x-wav')
        output.seek(0)
        return send_file(output, mimetype='audio/x-wav')
    else:
        return {}, status.HTTP_404_NOT_FOUND

@analysis_api.route("/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/waveform")
# @login_required
#@token_required
def get_json_waveform(run_id, original_file_node_id, audio_file_node_id, user: User = None):
    if not user:
        user = User(id_="stefano.dallona@gmail.com", email="stefano.dallona@gmail.com", name="Stefano")
    channel = request.args.get("channel", type=int, default=0)
    offset = request.args.get("offset", type=int, default=0)
    num_samples = request.args.get("num_samples", type=int, default=-1)
    max_slices = request.args.get("max_slices", type=int, default=3000)
    audio_file, plc_testbench = analysis_service.find_audio_file(
        run_id, audio_file_node_id, user, None, offset, num_samples, 'int32')
    downsampled_file = DownsampledAudioFile(audio_file, max_slices)
    downsampled_file.load(channel=channel, offset=0, n_samples=num_samples)
    '''
    # Reading wav frames as int
    from os.path import dirname, join as pjoin
    from scipy.io import wavfile
    import scipy.io
    samplerate, data = wavfile.read('C:\\Data\\plc-testbench-ui\\plc-testbench-ui\\original_tracks\\Blues_Guitar.wav')
    for i, value in enumerate(data):
    if i >= 441000 and i < 441000 + 10:
        frame = data[i]
        print(frame)
    '''
    
    if audio_file != None:
        
        # FIXME - to be normalized to int8
        return json.dumps({
            "version": 2,
            "channels": 1, #audio_file.channels,
            "sample_rate": audio_file.samplerate,
            "samples_per_pixel": math.ceil(len(audio_file.data) / max_slices),
            "bits": 8, #int(audio_file.subtype.replace("PCM_", "")),
            "length": len(downsampled_file.data) / 2 / 1,
            "data": [str(math.ceil(int(float(v)) / (256 * 256))) for k, v in downsampled_file.data.items()]
            }), status.HTTP_200_OK, {'Content-Type': 'application/json; charset=utf-8'}

    else:
        return {}, status.HTTP_404_NOT_FOUND

# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0/samples?channel=0&offset=1000000&num_samples=64
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/samples', methods=['GET'])
# @login_required
@token_required
def get_audio_file_samples(run_id, original_file_node_id, audio_file_node_id, user):
    channel = request.args.get("channel", type=int, default=0)
    offset = request.args.get("offset", type=int, default=0)
    num_samples = request.args.get("num_samples", type=int, default=1000)

    samples, plc_testbench = analysis_service.get_audio_file_samples(
        run_id, audio_file_node_id, channel, offset, num_samples, user=user)
    if samples != None:
        # return json.dumps(samples.data, default=samples.to_json()), status.HTTP_200_OK
        return json.dumps(samples.data, default=NpEncoder().default), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND

# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0/waveform?channel=0&offset=1000000&num_samples=200000&max_slices=3000


@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/waveform', methods=['GET'])
# @login_required
@token_required
def get_audio_file_waveform(run_id, original_file_node_id, audio_file_node_id, user):
    channel = request.args.get("channel", type=int, default=0)
    offset = request.args.get("offset", type=int, default=0)
    num_samples = request.args.get("num_samples", type=int, default=-1)
    max_slices = request.args.get("max_slices", type=int, default=3000)

    offset = None if offset == None or offset < 0 else offset
    num_samples = None if num_samples == None or num_samples < 0 else num_samples

    waveform, plc_testbench = analysis_service.get_audio_file_waveform(
        run_id, audio_file_node_id, max_slices, user, None, offset, num_samples)
    waveform.load(channel, offset, num_samples)
    if waveform != None:
        return json.dumps({
            "uuid": audio_file_node_id,
            "numSamples": waveform.num_samples,
            "duration": waveform.duration,
            "sampleRate": waveform.sample_rate,
            # "data": list(map(lambda x: str(x), waveform.data))
            "data": waveform.data
        }), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND


@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/waveforms', methods=['GET'])
# @login_required
@token_required
def get_audio_file_waveforms(run_id, original_file_node_id, user: User = None):
    channel = request.args.get("channel", type=int, default=0)
    offset = request.args.get("offset", type=int, default=0)
    num_samples = request.args.get("num_samples", type=int, default=-1)
    max_slices = request.args.get("max_slices", type=int, default=3000)

    offset = None if offset == None or offset < 0 else offset
    num_samples = None if num_samples == None or num_samples < 0 else num_samples

    run = analysis_service.ecctestbench_service.load_run(run_id, user)
    plc_testbench = analysis_service.ecctestbench_service.build_testbench_from_run(
        run, user, readonly=True)
    file_tree = analysis_service.__find_file_tree_by_node_id__(
        plc_testbench, original_file_node_id)
    audio_files = analysis_service.__find_audio_files__(file_tree)

    def retrieveWaveform(plc_testbench, audio_file_node_id) -> list:
        waveform, plc_testbench = analysis_service.get_audio_file_waveform(
            run_id, audio_file_node_id, max_slices, user, plc_testbench, offset, num_samples)
        waveform.load(channel, 0, num_samples)
        if waveform != None:
            return {
                "uuid": audio_file_node_id,
                "numSamples": waveform.num_samples,
                "duration": waveform.duration,
                "sampleRate": waveform.sample_rate,
                # "data": list(map(lambda x: str(x), waveform.data))
                "data": waveform.data
            }
    
    #audio_file_node_ids = list(map(lambda x: x.get_id(), audio_files[0:1]))
    audio_file_node_ids = list(map(lambda x: x.get_id(), audio_files))
    waveforms = list(map(functools.partial(
        retrieveWaveform, plc_testbench), audio_file_node_ids))
    if len(waveforms) > 0:
        return json.dumps(waveforms), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND

# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe
# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe?offset=100&num_samples=1000
# http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe?offset=100&num_samples=1000&unit_of_meas=seconds


@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/metrics/<metric_node_id>', methods=['GET'])
# @login_required
@token_required
def get_metric_samples(run_id, original_file_node_id, audio_file_node_id, metric_node_id, user):
    channel = request.args.get("channel", type=int, default=0)
    offset = request.args.get("offset", type=int, default=0)
    num_samples = request.args.get("num_samples", type=int)  # , default=1000)
    unit_of_meas = request.args.get(
        "unit_of_meas", type=str, default="samples")
    category = request.args.get("category", type=str)

    metric = analysis_service.get_metric_samples(run_id=run_id,
                                                 audio_file_node_id=audio_file_node_id,
                                                 metric_node_id=metric_node_id,
                                                 channel=channel,
                                                 offset=offset,
                                                 num_samples=num_samples,
                                                 unit_of_meas=unit_of_meas,
                                                 category=category,
                                                 user=user)
    if metric != None:
        return json.dumps(metric.data, default=DefaultJsonEncoder.to_json), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND
