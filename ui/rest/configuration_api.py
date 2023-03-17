from flask import Blueprint, json, request, make_response
from flask_api import status


from ..config.app_config import config
from ..services.configuration_service import ConfigurationService, UploadException



configuration_api = Blueprint("configuration", __name__, url_prefix="")
configuration_service = ConfigurationService(config.data_dir)

@configuration_api.route('/ecc_algorithms', methods=['GET'])
def ecc_algorithms():
  return json.dumps(configuration_service.find_ecc_algorithms()), status.HTTP_200_OK

@configuration_api.route('/loss_simulators', methods=['GET'])
def loss_simulators():
  return json.dumps(configuration_service.find_loss_simulators()), status.HTTP_200_OK

@configuration_api.route('/loss_models', methods=['GET'])
def loss_models():
  return json.dumps(configuration_service.find_loss_models()), status.HTTP_200_OK

@configuration_api.route('/output_analysers', methods=['GET'])
def output_analysers():
  return json.dumps(configuration_service.find_output_analysers()), status.HTTP_200_OK

@configuration_api.route('/settings_metadata', methods=['GET'])
def settings_metadata():
    return json.dumps(configuration_service.find_settings_metadata()), status.HTTP_200_OK

@configuration_api.route('/input_files', methods=['GET'])
def input_files():
  return json.dumps(configuration_service.find_input_files()), status.HTTP_200_OK

@configuration_api.route('/upload', methods=['POST'])
def upload():
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
