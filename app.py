from src import TrainPageGetter, StationsGetter, StationTimetableGetter, config
import json
from pprint import pprint
from flask import Flask, jsonify
app = Flask(__name__)

# Generate the station lookup table
config.global_station_list = {}
stations = StationsGetter.get_stations()
for station in stations:
    config.global_station_list[station["name"]] = station["station_id"]


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/train/<string:train_id>')
def get_train(train_id):
    train_list = TrainPageGetter.get_train(train_id)
    return jsonify(train_list)


@app.route('/get-stations/')
def get_stations():
    return jsonify(stations)


@app.route('/station/<int:station_id>')
def get_timetable(station_id):
    timetable = StationTimetableGetter.get_timetable(station_id)
    return jsonify(timetable)
