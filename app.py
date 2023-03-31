from flask import Flask, send_from_directory
from flask_cors import CORS
from waitress import serve

import logging

from logging.config import dictConfig

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

app = Flask(__name__,
            static_url_path='', 
            static_folder='static'
#            static_folder='build'
)
CORS(app)

from ui.rest.configuration_api import configuration_api
from ui.rest.execution_api import execution_api
from ui.rest.analysis_api import analysis_api

CORS(configuration_api)
CORS(execution_api)
CORS(analysis_api)

app.register_blueprint(configuration_api)
app.register_blueprint(execution_api)
app.register_blueprint(analysis_api)



@app.route('/')
def welcome():
    return '<h1>PLC TestBench UI up and running</h1>'
'''
@app.route("/")
def my_index():
    return send_from_directory(app.static_folder, 'index.html')
'''
if __name__ == '__main__':
    app.run(debug=True)
    #serve(app, host="0.0.0.0", port=5000, threads=10)