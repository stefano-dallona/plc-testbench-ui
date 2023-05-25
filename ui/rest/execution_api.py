
from flask import Blueprint, json, request, make_response, Response
from flask_api import status
from anytree.exporter import JsonExporter

from ..repositories.run_repository import *
from ..config.app_config import *
from ..services.ecctestbench_service import *
from ..services.execution_service import *
from ..models.run import *
from ..rest.streaming_api import get_socketio
from redbird.repos import MongoRepo
from pymongo import MongoClient
from pydantic import BaseModel

class MyItem(BaseModel):
    _id: str

client=MongoClient(config.db_conn_string)
run_repository_mongodb = MongoRepo(uri=config.db_conn_string, database=config.db_name, collection="OriginalTrack-3", model=dict)


execution_api = Blueprint("execution", __name__, url_prefix="")
run_repository = RunRepository(config.data_dir)
ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository, socketio=get_socketio())
execution_service = ExecutionService(ecctestbench_service, run_repository)

@execution_api.route('/runs', methods=['GET'])
def get_runs():
    page = int(request.args.get('page')) if request.args.get('page') != None else 0
    page_size = int(request.args.get('page_size')) if request.args.get('page_size') != None else -1
    runs = execution_service.get_runs()
    start = max(0, page - 1) * page_size
    end = min(len(runs), (page + 1) * page_size)
    end = end if end >= 0 else len(runs)
    return json.dumps(runs[start:end]), 200
  
@execution_api.route('/runs/searches', methods=['POST'])
def search_runs():
    search = request.json
    query = search["queryString"]
    projection = search["projectionString"]
    pagination = search["pagination"]
    cursor = client.get_database("plc_database").get_collection("OriginalTrack-3")  \
      .find(query, projection=projection) \
      .skip(pagination["page"] * pagination["pageSize"]) \
      .limit(pagination["pageSize"])
    runs = list(cursor)
    for run in runs:
      print(run)
    return json.dumps(runs), 200

@execution_api.route('/runs', methods=['POST'])
def create_run():
    run_id = str(uuid.uuid4())
    run = ecctestbench_service.create_run(request.json, run_id)
    ecctestbench_service.save_run(run)
    run = ecctestbench_service.load_run(run.run_id)
    return json.dumps({"run_id": run.run_id}), 200

@execution_api.route('/runs/<run_id>/executions', methods=['POST'])
def launch_run_execution(run_id):
    execution = RunExecution(run_id=run_id)
    execution.execution_id = ecctestbench_service.launch_run_execution(run_id)
    run = ecctestbench_service.load_run(run_id)
    run.status = RunStatus.RUNNING
    ecctestbench_service.save_run(run)
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
