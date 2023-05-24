#from gevent import monkey
#monkey.patch_all()
import eventlet
eventlet.monkey_patch()
from flask import Flask, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from waitress import serve
from eventlet import wsgi

import tqdm
import logging
from logging.config import dictConfig

from ui.rest.streaming_api import *

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
    
    CORS(app)
    CORS(configuration_api)
    CORS(execution_api)
    CORS(analysis_api)
    CORS(streaming_api)
    
    app.register_blueprint(configuration_api)
    app.register_blueprint(execution_api)
    app.register_blueprint(analysis_api)
    app.register_blueprint(streaming_api)
    
    get_socketio().init_app(app)
           
    return app

app = create_app()

@app.route('/')
def welcome():
    return '<h1>PLC TestBench UI up and running</h1>'


if __name__ == '__main__':
    #https://github.com/miguelgrinberg/python-socketio/discussions/860
    get_socketio().run(app, host='0.0.0.0', use_reloader=False)
    #serve(app, host="0.0.0.0", port=5000, threads=10)
    #eventlet.wsgi.server(eventlet.listen(("127.0.0.1", 5000)), app, debug=True)