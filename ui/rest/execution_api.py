
from flask import Blueprint, json, request, make_response, Response
from flask_api import status
from anytree.exporter import JsonExporter

from ..repositories.run_repository import *
from ..config.app_config import *
from ..services.ecctestbench_service import *
from ..services.execution_service import *
from ..models.run import *


execution_api = Blueprint("execution", __name__, url_prefix="")
ecctestbench_service = EccTestbenchService(run_repository=RunRepository(config.data_dir))
execution_service = ExecutionService(ecctestbench_service)

@execution_api.route('/runs', methods=['POST'])
def runs():
    run_id = str(uuid.uuid4())
    run = ecctestbench_service.create_run(request.json, run_id)
    ecctestbench_service.save_run(run)
    run = ecctestbench_service.load_run(run.run_id)
    return json.dumps({"run_id": run.run_id}), 200

@execution_api.route('/runs/<run_id>/executions', methods=['POST'])
def launch_run_execution(run_id):
    execution = RunExecution(run_id=run_id)
    execution.execution_id = ecctestbench_service.launch_run_execution(run_id)
    return json.dumps({"execution_id": execution.execution_id}), status.HTTP_201_CREATED
  
@execution_api.route('/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    run = ecctestbench_service.load_run(run_id)
    if run != None:
      return json.dumps({ "run_id": run.run_id, "selected_input_files": run.selected_input_files}), status.HTTP_200_OK
    else:
      return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/executions/76728771-9de8-42bd-a71e-f4d3c08e3ae6/hierarchy
@execution_api.route('/runs/<run_id>/executions/<execution_id>/hierarchy', methods=['GET'])
def get_execution_hierarchy(run_id: str, execution_id: str):
  hierarchy = execution_service.get_execution_hierarchy(run_id=run_id, execution_id=execution_id)
  if hierarchy != None:
    exporter = JsonExporter(indent=2)
    return json.dumps([json.loads(exporter.export(root_node)) for root_node in hierarchy]), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/executions/76728771-9de8-42bd-a71e-f4d3c08e3ae6/events
@execution_api.route('/runs/<run_id>/executions/<execution_id>/events', methods=['GET'])
def get_execution_events(run_id: str, execution_id: str):
  events = execution_service.get_execution_events(run_id=run_id, execution_id=execution_id)
  return Response(events, mimetype='text/event-stream')
