
from flask import Blueprint, json, request, make_response, Response
from flask_api import status
from anytree.exporter import JsonExporter
from flask_login import login_required

from redbird.repos import MongoRepo
from pymongo import MongoClient
from pydantic import BaseModel

from ..repositories.pickle.run_repository import RunRepository
from ..repositories.mongodb.run_repository import RunRepository as MongoRunRepository
from ..config.app_config import *
from ..services.ecctestbench_service import *
from ..services.execution_service import *
from ..models.run import *
from ..rest.streaming_api import get_socketio
from ..services.authentication_service import token_required


class MyItem(BaseModel):
    _id: str

client=MongoClient(config.db_conn_string)
run_repository_mongodb = MongoRepo(uri=config.db_conn_string, database=config.db_name, collection="OriginalTrack-3", model=dict)
run_repository_mongodb2 = MongoRunRepository(client)


execution_api = Blueprint("execution", __name__, url_prefix="")
run_repository = RunRepository(config.data_dir)
ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository, socketio=get_socketio())
execution_service = ExecutionService(ecctestbench_service, run_repository)

@execution_api.route('/runs', methods=['GET'])
#@login_required
@token_required
def get_runs():
    page = int(request.args.get('page')) if request.args.get('page') != None else 0
    page_size = int(request.args.get('page_size')) if request.args.get('page_size') != None else -1
    pagination = { 'page': page, 'pageSize': page_size }
    runs = execution_service.get_runs(pagination)
    return json.dumps({ 'data': runs['data'], 'totalRecords': runs['totalRecords'] }), 200
  
@execution_api.route('/runs/searches', methods=['POST'])
#@login_required
@token_required
def search_runs():
    search = json.loads(request.json['body'])
    query = search["queryString"]
    projection = search["projectionString"]
    pagination = search["pagination"]      
    runs = run_repository_mongodb2.find_by_query(query=query,
                                          projection=projection,
                                          pagination=pagination)
    return json.dumps(runs), 200

@execution_api.route('/runs', methods=['POST'])
#@login_required
@token_required
def create_run():
    run_id = str(uuid.uuid4())
    payload = json.loads(request.json["body"])
    run = ecctestbench_service.create_run(payload, run_id)
    ecctestbench_service.save_run(run)
    run = ecctestbench_service.load_run(run.run_id)
    return json.dumps({"run_id": run.run_id}), 200

@execution_api.route('/runs/<run_id>/executions', methods=['POST'])
#@login_required
#@token_required
def launch_run_execution(run_id):
    execution = RunExecution(run_id=run_id)
    execution.execution_id = ecctestbench_service.launch_run_execution(run_id)
    run = ecctestbench_service.load_run(run_id)
    run.status = RunStatus.RUNNING
    ecctestbench_service.save_run(run)
    return json.dumps({"execution_id": execution.execution_id}), status.HTTP_201_CREATED
  
@execution_api.route('/runs/<run_id>', methods=['GET'])
#@login_required
@token_required
def get_run(run_id):
    run = ecctestbench_service.load_run(run_id)
    if run != None:
      return json.dumps({ "run_id": run.run_id, "selected_input_files": run.selected_input_files}), status.HTTP_200_OK
    else:
      return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/executions/76728771-9de8-42bd-a71e-f4d3c08e3ae6/hierarchy
@execution_api.route('/runs/<run_id>/executions/<execution_id>/hierarchy', methods=['GET'])
#@login_required
@token_required
def get_execution_hierarchy(run_id: str, execution_id: str):
  hierarchy = execution_service.get_execution_hierarchy(run_id=run_id, execution_id=execution_id)
  if hierarchy != None:
    exporter = JsonExporter(indent=2)
    return json.dumps([json.loads(exporter.export(root_node)) for root_node in hierarchy]), status.HTTP_200_OK
  else:
    return {}, status.HTTP_404_NOT_FOUND

#http://localhost:5000/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/executions/76728771-9de8-42bd-a71e-f4d3c08e3ae6/events
@execution_api.route('/runs/<run_id>/executions/<execution_id>/events', methods=['GET'])
#@login_required
#@token_required
def get_execution_events(run_id: str, execution_id: str):
  events = execution_service.get_execution_events(run_id=run_id, execution_id=execution_id)
  return Response(events, mimetype='text/event-stream')
