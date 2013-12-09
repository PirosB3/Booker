import datetime
import json
import os
import time

import pymongo

from flask import Flask, render_template
from pymongo.uri_parser import parse_uri

# Define environment variables
DEBUG = os.environ.get('ENVIRONMENT_TYPE', 'debug') == 'debug'
MONGO_URL = os.environ.get('MONGOHQ_URL', 'mongodb://localhost/booker')

# Define persistence layer
conn = pymongo.Connection(MONGO_URL)
db = conn[parse_uri(MONGO_URL)['database']]
persistence = db['bookings']

# Define web server
app = Flask(__name__)
app.config.from_object(__name__)

# Define constants and helper functions
to_dict = lambda k: {'name': k['name'], 'status': k['status'], 'date': k['datetime'].ctime()}

@app.route('/bookings')
def bookings():
    bookings = map(to_dict, persistence.find())
    return json.dumps(bookings)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
