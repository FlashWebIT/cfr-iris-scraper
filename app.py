from src import TrainPageGetter, StationsGetter, StationTimetableGetter
import json
from pprint import pprint
from flask import Flask, jsonify
app = Flask(__name__)

global_station_list = StationsGetter.get_stations();

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/train/<int:train_id>')
def get_train(train_id):
    train_list = TrainPageGetter.get_train(train_id)
    return jsonify(train_list)

@app.route('/get-stations/')
def get_stations():
    return jsonify(global_station_list)\

@app.route('/station/<int:station_id>')
def get_timetable(station_id):
    timetable = StationTimetableGetter.get_timetable(station_id)
    return jsonify(timetable)

#TrainPageGetter.get_train(15594)
#TrainPageGetter.get_train(1684)
#TrainPageGetter.get_train(15531)
#pprint(StationTimetableGetter.get_timetable(10017))
