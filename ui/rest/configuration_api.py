from flask import Blueprint, json, request, make_response
from flask_api import status
from flask_login import login_required


from ..config.app_config import config
from ..services.configuration_service import ConfigurationService, UploadException, DuplicatedKeyException, ValidationException, KeyNotFoundException
from ..services.authentication_service import token_required
from ..models.filter import *
from ..repositories.mongodb.filter_repository import *


configuration_api = Blueprint("configuration", __name__, url_prefix="")
filter_repository = FilterRepository()
configuration_service = ConfigurationService(config.data_dir, filter_repository)

@configuration_api.route('/ecc_algorithms', methods=['GET'])
#@login_required
@token_required
def ecc_algorithms(user):
  return json.dumps(configuration_service.find_ecc_algorithms()), status.HTTP_200_OK

@configuration_api.route('/loss_simulators', methods=['GET'])
#@login_required
@token_required
def loss_simulators(user):
  return json.dumps(configuration_service.find_loss_simulators()), status.HTTP_200_OK

@configuration_api.route('/loss_models', methods=['GET'])
#@login_required
@token_required
def loss_models(user):
  return json.dumps(configuration_service.find_loss_models()), status.HTTP_200_OK

@configuration_api.route('/output_analysers', methods=['GET'])
#@login_required
@token_required
def output_analysers(user):
  category = request.args.get("category", type=str, default=None)
  return json.dumps(configuration_service.find_output_analysers(category)), status.HTTP_200_OK

@configuration_api.route('/settings_metadata', methods=['PUT'])
#@login_required
@token_required
def recalculate_metadata(user = None):
  settings_list = request.get_json()
  modified_setting = request.args.get("modified_setting", type=str, default=None)
  new_value = json.loads(request.args.get("new_value", type=str, default=None))
  valueType = new_value["data"]["valueType"]
  
  settings = None
  if settings_list:
    settings_groups = [settings for settings in configuration_service.parse_settings_from_json(settings_list).values() if settings and len(settings) > 0]
    settings_type = settings_groups[0]
    settings_tuple = settings_type[0]
    settings = settings_tuple[1]
  
  new_value = new_value["data"]["value"] if valueType not in ["settingsList", "dictionary"] else new_value
  conversion_function = configuration_service.get_conversion_function(valueType, settings_list, new_value, modified_setting, type(settings_tuple[1]))
  new_value = conversion_function(new_value)

  return json.dumps(configuration_service.find_settings_metadata([settings], modified_setting, new_value)), status.HTTP_200_OK

@configuration_api.route('/settings/validate', methods=['PUT'])
#@login_required
@token_required
def validate_settings(user = None):
  settings_list = request.get_json()
  errors = configuration_service.validate_settings([settings_list])
  return json.dumps({} if len(errors) == 0 else { "errors": errors }), status.HTTP_200_OK

@configuration_api.route('/settings_metadata', methods=['GET'])
#@login_required
@token_required
def settings_metadata(user = None):
  return json.dumps(configuration_service.find_settings_metadata()), status.HTTP_200_OK
  
@configuration_api.route('/search_fields', methods=['GET'])
#@login_required
@token_required
def search_fields(user = None):
  return json.dumps(configuration_service.get_search_fields()), status.HTTP_200_OK
  
@configuration_api.route('/filters', methods=['POST'])
#@login_required
@token_required
def save_filter(user = None):
  filter = Filter(**request.json["body"])
  try:
    result = configuration_service.save_filter(filter, user)
    return json.dumps(result, default=DefaultJsonEncoder.to_json), status.HTTP_200_OK
  except DuplicatedKeyException:
    return "Filter name must be unique", status.HTTP_409_CONFLICT

@configuration_api.route('/filters/<filter_id>', methods=['DELETE'])
#@login_required
@token_required
def delete_filter(filter_id, user = None):
  try:
    result = configuration_service.delete_filter(filter_id, user)
    return json.dumps(result, default=DefaultJsonEncoder.to_json), status.HTTP_200_OK
  except KeyNotFoundException:
    return "Filter not found", status.HTTP_404_NOT_FOUND

@configuration_api.route('/filters', methods=['GET'])
#@login_required
@token_required
def find_filters(user = None):
  name = request.args.get("name", type=str, default=None)
  return json.dumps(configuration_service.find_filters({name: name} if name else {}, user), default=DefaultJsonEncoder.to_json), status.HTTP_200_OK

@configuration_api.route('/input_files', methods=['GET'])
#@login_required
@token_required
def input_files(user):
  return json.dumps(configuration_service.find_input_files()), status.HTTP_200_OK

@configuration_api.route('/upload', methods=['POST'])
#@login_required
@token_required
def upload(user):
    file = request.files['file']
    total_file_size = int(request.form['dztotalfilesize'])
    chunk_index = int(request.form['dzchunkindex'])
    chunk_offset = int(request.form['dzchunkbyteoffset'])
    total_chunks = int(request.form['dztotalchunkcount'])
    
    try:
        configuration_service.upload_audio_files(file, total_file_size, total_chunks, chunk_index, chunk_offset)
        return make_response("Chunk upload successful", status.HTTP_201_CREATED)
    except UploadException as e:
        return make_response(str(e), 500)

@configuration_api.route('/validation/workers', methods=['POST'])
#@login_required
@token_required
def validate_worker(user):
  worker = request.json["body"]
  try:
    return json.dumps(configuration_service.validate_worker(worker)), status.HTTP_200_OK
  except ValidationException as ex:
    return json.dumps(str(ex)), status.HTTP_400_BAD_REQUEST
