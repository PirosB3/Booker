import datetime
import json
import os
import time

import pymongo

from flask import Flask, render_template
from pymongo.uri_parser import parse_uri

DEBUG = os.environ.get('ENVIRONMENT_TYPE', 'debug') == 'debug'
MONGO_URL = os.environ.get('MONGOHQ_URL', 'mongodb://localhost/booker')

conn = pymongo.Connection(MONGO_URL)
db = conn[parse_uri(MONGO_URL)['database']]
persistence = db['bookings']

app = Flask(__name__)
app.config.from_object(__name__)

EPOCH = 1000

to_dict = lambda k: {'name': k['name'], 'status': k['status'], 'date': date_to_millis(k['datetime'])}

def date_to_millis(d):
    return time.mktime(d.timetuple()) * EPOCH

@app.route('/bookings')
def bookings():
    bookings = map(to_dict, persistence.find())
    return json.dumps(bookings)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
