
from flask import Blueprint, json, request, make_response, Response, session
from flask_api import status
from anytree.exporter import JsonExporter
from flask_login import login_required
import uuid
import time
import logging
import traceback

from redbird.repos import MongoRepo
from pymongo import MongoClient
from pydantic import BaseModel

from ..repositories.pickle.run_repository import RunRepository
from ..repositories.mongodb.run_repository import RunRepository as MongoRunRepository
from ..config.app_config import *
from ..services.plctestbench_service import *
from ..services.execution_service import *
from ..services.authentication_service import *
from ..models.run import *
from ..rest.streaming_api import get_socketio
from ..services.authentication_service import token_required


class MyItem(BaseModel):
    _id: str


run_repository_mongodb2 = MongoRunRepository()


execution_api = Blueprint("execution", __name__, url_prefix="")
run_repository = RunRepository(config.data_dir)
# ecctestbench_service = EccTestbenchService(config.data_dir, run_repository=run_repository, socketio=get_socketio())
ecctestbench_service = EccTestbenchService(
    config.data_dir, run_repository=run_repository_mongodb2, socketio=get_socketio())
# execution_service = ExecutionService(ecctestbench_service, run_repository)
execution_service = ExecutionService(
    ecctestbench_service, run_repository=run_repository_mongodb2)

logger = logging.getLogger()


@execution_api.route('/runs', methods=['GET'])
# @login_required
@token_required
def get_runs(user):
    # logger.info(f"Start retrieving runs ...")
    page = int(request.args.get('page')) if request.args.get(
        'page') != None else 0
    page_size = int(request.args.get('page_size')) if request.args.get(
        'page_size') != None else -1
    pagination = {'page': page, 'pageSize': page_size}
    # logger.info(f"Calling execution service")
    runs = execution_service.get_runs(pagination, user)
    # logger.info(f"Finished calling execution service")
    # raise Exception("Test exception")
    return json.dumps({'data': runs['data'], 'totalRecords': runs['totalRecords']}, default=lambda o: o.__class__.__name__ if isinstance(o, type) else o.__dict__), 200


@execution_api.route('/runs/searches', methods=['POST'])
# @login_required
@token_required
def search_runs(user):
    try:
        search = json.loads(request.json['body'])
        query = json.loads(search["queryString"])
        projection = search["projectionString"]
        pagination = search["pagination"]

        runs = run_repository_mongodb2.find_by_filter(filters=query,
                                                      projection=projection,
                                                      pagination=pagination,
                                                      user=user)
        return json.dumps(runs), status.HTTP_200_OK
    except Exception:
        return "Invalid search", status.HTTP_404_NOT_FOUND


@execution_api.route('/runs', methods=['POST'])
# @login_required
@token_required
def create_run(user):
    # run_id = str(uuid.uuid4())
    payload = json.loads(request.json["body"])
    # run = ecctestbench_service.create_run(payload, run_id)
    run = ecctestbench_service.create_run(payload, None, user)
    # ecctestbench_service.save_run(run)
    # run = ecctestbench_service.load_run(run.run_id)
    return json.dumps({"run_id": str(run.run_id)}), 200


@execution_api.route('/runs/<run_id>/executions', methods=['POST'])
# @login_required
@token_required
def launch_run_execution(run_id, user):
    task_id = request.get_json()["body"]["task_id"]
    execution = RunExecution(run_id=run_id)
    execution.execution_id = ecctestbench_service.launch_run_execution(
        run_id, user=user, task_id=task_id)
    run = ecctestbench_service.load_run(run_id, user=user)
    # run.status = RunStatus.RUNNING
    # ecctestbench_service.save_run(run)
    return json.dumps({"execution_id": execution.execution_id}), status.HTTP_201_CREATED


@execution_api.route('/runs/<run_id>', methods=['GET'])
# @login_required
@token_required
def get_run(run_id, user):
    run = ecctestbench_service.load_run(run_id, user=user)
    if run != None:
        return json.dumps(run, default=lambda o: o.__dict__), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND

# http://localhost:5000/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/executions/76728771-9de8-42bd-a71e-f4d3c08e3ae6/hierarchy


@execution_api.route('/runs/<run_id>/executions/<execution_id>/hierarchy', methods=['GET'])
# @login_required
@token_required
def get_execution_hierarchy(run_id: str, execution_id: str, user):
    hierarchy = execution_service.get_execution_hierarchy(
        run_id=run_id, execution_id=execution_id, user=user)
    if hierarchy != None:
        exporter = JsonExporter(indent=2)
        return json.dumps([json.loads(exporter.export(root_node)) for root_node in hierarchy]), status.HTTP_200_OK
    else:
        return {}, status.HTTP_404_NOT_FOUND

# http://localhost:5000/runs/76728771-9de8-42bd-a71e-f4d3c08e3ae6/executions/76728771-9de8-42bd-a71e-f4d3c08e3ae6/events


@execution_api.route('/runs/<run_id>/executions/<execution_id>/events', methods=['GET'])
# @login_required
@token_required
def get_execution_events(run_id: str, execution_id: str, user):
    # def get_execution_events(run_id: str, execution_id: str):
    task_id = request.args.get("task_id")
    last_event_id = request.headers.get("Last-Event-ID")
    user = None
    '''
  token = request.args["token"]
  if not token:
    return {
        "message": "Authentication Token is missing!",
        "data": None,
        "error": "Unauthorized"
    }, 401
  try:
    user = get_user_from_jwt_token(token)
  except TokenDecodingException as ex:
    return {
        "message": "Could not decode token!",
        "data": None,
        "error": str(ex)
    }, 401
  '''
    events = execution_service.get_execution_events(task_id=task_id,
                                                    run_id=run_id,
                                                    execution_id=execution_id,
                                                    last_event_id=last_event_id,
                                                    user=user)
    headers = {
        #  'X-Accel-Buffering': 'no',
        #  'Last-Modified': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
    }
    response = Response(events, mimetype='text/event-stream', headers=headers)
    return response


@execution_api.route('/notifications', methods=['GET'])
# @login_required
@token_required
def get_notifications(user=None):
    try:
        run_ids = [str(run_id) for run_id in request.args.get("run_ids").split(",")]
        query = {
            "_id": {
              "$in": run_ids
            },
            "status": {
              "$in": ["COMPLETED", "FAILED"]
            }
        }
        projection = {
            "_id": 1,
            "status": 1,
            "created_on": 1
        }
        notifications = run_repository_mongodb2.find_by_filter(filters=query,
                                                      projection=projection,
                                                      pagination=None,
                                                      user=user)
        notifications = list(map(lambda notification: {
          "uuid": notification["_id"],
          "severity": "success" if notification["status"] == "COMPLETED" else "error",
          "text": f"Run '{notification['_id']}' created on {notification['created_on']} {'completed successfully' if notification['status'] == 'COMPLETED' else 'failed'}"
        }, notifications["data"]))
        return json.dumps(notifications), status.HTTP_200_OK
    except Exception:
        return "Invalid notifications search", status.HTTP_404_NOT_FOUND
