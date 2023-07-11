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

from .streaming_api import stream_audio_file as stream_file
from ..services.authentication_service import token_required

run_repository = RunRepository(config.data_dir)

run_repository_mongodb2 = MongoRunRepository()

#ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository)
ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository_mongodb2)
analysis_api = Blueprint("analysis", __name__, url_prefix="/analysis")
analysis_service = AnalysisService(ecctestbench_service=ecctestbench_service)


#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/loss-simulations/0b06e77f-2228-4b54-b78b-955602e32dc5
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/loss-simulations/<loss_simulation_node_id>', methods=['GET'])
#@login_required
@token_required
def find_lost_samples(run_id, original_file_node_id, loss_simulation_node_id, user):
  unit_of_meas = request.args.get('unit_of_meas')
  unit_of_meas = unit_of_meas if unit_of_meas != None else "samples"
  
  current_app.logger.info(f"Retrieving lost samples from run_id {run_id} and file {original_file_node_id} and loss simulation {loss_simulation_node_id}")
  lost_samples = analysis_service.find_lost_samples(run_id, original_file_node_id, loss_simulation_node_id, unit_of_meas, user)
  if lost_samples != None:
    return json.dumps(lost_samples, default=lost_samples.to_json()), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0
@analysis_api.route("/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>")
#@login_required
@token_required
def stream_audio_file(run_id, original_file_node_id, audio_file_node_id, user):
  audio_file = analysis_service.find_audio_file(run_id, audio_file_node_id, user)
  if audio_file != None:
    return send_file(audio_file.path, mimetype='audio/x-wav')
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0/samples?channel=0&offset=1000000&num_samples=64
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/samples', methods=['GET'])
#@login_required
@token_required
def get_audio_file_samples(run_id, original_file_node_id, audio_file_node_id, user):
  channel = request.args.get("channel", type=int, default=0)
  offset = request.args.get("offset", type=int, default=0)
  num_samples = request.args.get("num_samples", type=int, default=1000)
  
  samples = analysis_service.get_audio_file_samples(run_id, audio_file_node_id, channel, offset, num_samples, user=user)
  if samples != None:
    #return json.dumps(samples.data, default=samples.to_json()), status.HTTP_200_OK
    return json.dumps(samples.data, default=NpEncoder().default), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND
  
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0/waveform?channel=0&offset=1000000&num_samples=200000&max_slices=3000
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/waveform', methods=['GET'])
#@login_required
@token_required
def get_audio_file_waveform(run_id, original_file_node_id, audio_file_node_id, user):
  channel = request.args.get("channel", type=int, default=0)
  offset = request.args.get("offset", type=int, default=0)
  num_samples = request.args.get("num_samples", type=int, default=1000)
  max_slices = request.args.get("max_slices", type=int, default=3000)
  
  offset = None if offset == None or offset < 0 else offset
  num_samples = None if num_samples == None or num_samples < 0 else num_samples
  
  waveform = analysis_service.get_audio_file_waveform(run_id, audio_file_node_id, max_slices, user)
  waveform.load(channel, offset, num_samples)
  if waveform != None:
    return json.dumps({
                        "uuid": audio_file_node_id,
                        "numSamples": waveform.num_samples,
                        "duration": waveform.duration,
                        "sampleRate": waveform.sample_rate,
                        #"data": list(map(lambda x: str(x), waveform.data))
                        "data": waveform.data
                      }), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe?offset=100&num_samples=1000
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe?offset=100&num_samples=1000&unit_of_meas=seconds
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/metrics/<metric_node_id>', methods=['GET'])
#@login_required
@token_required
def get_metric_samples(run_id, original_file_node_id, audio_file_node_id, metric_node_id, user):
  channel = request.args.get("channel", type=int, default=0)
  offset = request.args.get("offset", type=int, default=0)
  num_samples = request.args.get("num_samples", type=int) #, default=1000)
  unit_of_meas = request.args.get("unit_of_meas", type=str, default="samples")
  category = request.args.get("category", type=str)
  
  metric = analysis_service.get_metric_samples(run_id = run_id,
                                               audio_file_node_id=audio_file_node_id,
                                               metric_node_id = metric_node_id,
                                               channel = channel,
                                               offset = offset,
                                               num_samples = num_samples,
                                               unit_of_meas = unit_of_meas,
                                               category=category,
                                               user=user)
  if metric != None:
    return json.dumps(metric.data, default=metric.to_json()), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND