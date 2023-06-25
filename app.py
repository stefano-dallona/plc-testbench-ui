#from gevent import monkey
#monkey.patch_all()
import eventlet

from ui.models.user import User

eventlet.monkey_patch()
from flask import Flask, Response, send_from_directory, request, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from waitress import serve
from eventlet import wsgi

from flask_login import LoginManager, current_user, login_required, login_user, logout_user

import logging
from logging.config import dictConfig

from ui.rest.streaming_api import *
from ui.services.authentication_service import token_required

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s(): %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

logging.basicConfig(level=logging.DEBUG)

login_manager = LoginManager()

def create_app():
    
    app = Flask(__name__,
                static_url_path='', 
                static_folder='static',
    #            static_folder='build'
    )
    
    from ui.rest.configuration_api import configuration_api
    from ui.rest.execution_api import execution_api
    from ui.rest.analysis_api import analysis_api
    from ui.rest.streaming_api import streaming_api
    from ui.rest.authentication_api import authentication_api
    
    CORS(app)
    CORS(configuration_api)
    CORS(execution_api)
    CORS(analysis_api)
    CORS(streaming_api)
    CORS(authentication_api)
    
    app.register_blueprint(configuration_api)
    app.register_blueprint(execution_api)
    app.register_blueprint(analysis_api)
    app.register_blueprint(streaming_api)
    app.register_blueprint(authentication_api)
    
    get_socketio().init_app(app)
    
    login_manager.init_app(app)
           
    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
@token_required
def index():
    return '<h1>PLC TestBench UI up and running</h1>'        
    
@app.route('/home')
#@login_required
@token_required
def home():
    return '<h1>PLC TestBench UI up and running</h1>'        


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    #https://github.com/miguelgrinberg/python-socketio/discussions/860
    get_socketio().run(app, host='127.0.0.1', use_reloader=False, certfile="secrets/cert.pem", keyfile="secrets/key.pem")
    #serve(app, host="0.0.0.0", port=5000, threads=10)
    #eventlet.wsgi.server(eventlet.listen(("127.0.0.1", 5000)), app, debug=True)