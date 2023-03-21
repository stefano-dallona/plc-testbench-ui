from flask import Blueprint, json, request, make_response, send_file
from flask import current_app
from flask_api import status

from ..config.app_config import config
from ..repositories.run_repository import RunRepository
from ..services.analysis_service import AnalysisService
from ..services.ecctestbench_service import EccTestbenchService
from ..models.base_model import *

run_repository = RunRepository(config.data_dir)
ecctestbench_service = EccTestbenchService(run_repository=run_repository)
analysis_api = Blueprint("analysis", __name__, url_prefix="/analysis")
analysis_service = AnalysisService(ecctestbench_service=ecctestbench_service)

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/loss-simulations/0b06e77f-2228-4b54-b78b-955602e32dc5
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/loss-simulations/<loss_simulation_node_id>', methods=['GET'])
def find_lost_samples(run_id, original_file_node_id, loss_simulation_node_id):
  unit_of_meas = request.args.get('unit_of_meas')
  unit_of_meas = unit_of_meas if unit_of_meas != None else "samples"
  
  current_app.logger.info(f"Retrieving lost samples from run_id {run_id} and file {original_file_node_id} and loss simulation {loss_simulation_node_id}")
  lost_samples = analysis_service.find_lost_samples(run_id, original_file_node_id, loss_simulation_node_id, unit_of_meas)
  if lost_samples != None:
    return json.dumps(lost_samples, default=lost_samples.to_json()), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0
@analysis_api.route("/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>")
def stream_audio_file(run_id, original_file_node_id, audio_file_node_id):
  audio_file = analysis_service.find_audio_file(run_id, audio_file_node_id)
  if audio_file != None:
    return send_file(audio_file.path, mimetype='audio/x-wav')
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/76f9743b-d839-4e64-bf55-01f86107bec0/samples?channel=0&offset=1000000&num_samples=64
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/samples', methods=['GET'])
def get_audio_file_samples(run_id, original_file_node_id, audio_file_node_id):
  channel = request.args.get("channel", type=int, default=0)
  offset = request.args.get("offset", type=int, default=0)
  num_samples = request.args.get("num_samples", type=int, default=1000)
  
  samples = analysis_service.get_audio_file_samples(run_id, audio_file_node_id, channel, offset, num_samples)
  if samples != None:
    return json.dumps(samples.data, default=samples.to_json()), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe?offset=100&num_samples=1000
#http://localhost:5000/analysis/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/input-files/76f9743b-d839-4e64-bf55-01f86107bec0/output-files/eb7a511c-8258-440c-bd81-e4cd38472cd7/metrics/37642fbf-2fa5-45d2-8afe-dcfb78b85cbe?offset=100&num_samples=1000&unit_of_meas=seconds
@analysis_api.route('/runs/<run_id>/input-files/<original_file_node_id>/output-files/<audio_file_node_id>/metrics/<metric_id>', methods=['GET'])
def get_metric_samples(run_id, original_file_node_id, audio_file_node_id, metric_id):
  channel = request.args.get("channel", type=int, default=0)
  offset = request.args.get("offset", type=int, default=0)
  num_samples = request.args.get("num_samples", type=int, default=1000)
  unit_of_meas = request.args.get("unit_of_meas", type=str, default="samples")
  
  metric = analysis_service.get_metric_samples(run_id=run_id,
                                               original_file_node_id=original_file_node_id,
                                               metric_node_id=metric_id,
                                               channel=channel,
                                               offset=offset,
                                               num_samples=num_samples,
                                               unit_of_meas=unit_of_meas)
  if metric != None:
    return json.dumps(metric.data), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND