from src import TrainPageGetter, StationsGetter, StationTimetableGetter, config
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from dateutil import tz, parser

app = Flask(__name__)
CORS(app)

# Generate the station lookup table
config.global_station_list = {}
stations = StationsGetter.get_stations()
for station in stations:
    config.global_station_list[station["name"]] = station["station_id"]

@app.route('/static/<path:path>')
def send_res(path):
    return send_from_directory('static', path)

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


def timetable_departures_filter(timetable):
    departures_timetable = []

    for item in timetable:
        if item['is_origin'] or item['is_stop']:
            departures_timetable.append(item)

    return departures_timetable


def timetable_arrivals_filter(timetable):
    departures_timetable = []

    for item in timetable:
        if item['is_destination'] or item['is_stop']:
            departures_timetable.append(item)

    return departures_timetable


def timestamp_current_filter(timetable):
    current_timetable = []

    for item in timetable:
        timezone = tz.gettz('Europe/Bucharest')
        beginning = datetime.now(tz=timezone) - timedelta(hours=1)
        end = datetime.now(tz=timezone) + timedelta(hours=3)

        if item['arrival_timestamp']:
            arrival = parser.isoparse(item['arrival_timestamp'])

            if beginning <= arrival <= end:
                current_timetable.append(item)
                continue

            if beginning <= arrival + timedelta(minutes=item['delay']) <= end:
                current_timetable.append(item)
                continue

        if item['departure_timestamp']:
            departure = parser.isoparse(item['departure_timestamp'])

            if beginning <= departure <= end:
                current_timetable.append(item)
                continue

            if beginning <= departure + timedelta(minutes=item['delay']) <= end:
                current_timetable.append(item)
                continue

    return current_timetable

@app.route('/station/<int:station_id>/departures')
def get_departures_timetable(station_id):
    timetable = StationTimetableGetter.get_timetable(station_id)
    timetable = timetable_departures_filter(timetable)
    return jsonify(timetable)


@app.route('/station/<int:station_id>/departures/current')
def get_current_departures_timetable(station_id):
    timetable = StationTimetableGetter.get_timetable(station_id)
    timetable = timestamp_current_filter(timetable)
    timetable = timetable_departures_filter(timetable)
    return jsonify(timetable)


@app.route('/station/<int:station_id>/arrivals')
def get_arrivals_timetable(station_id):
    timetable = StationTimetableGetter.get_timetable(station_id)
    timetable = timetable_arrivals_filter(timetable)
    return jsonify(timetable)


@app.route('/station/<int:station_id>/arrivals/current')
def get_current_arrivals_timetable(station_id):
    timetable = StationTimetableGetter.get_timetable(station_id)
    timetable = timestamp_current_filter(timetable)
    timetable = timetable_arrivals_filter(timetable)
    return jsonify(timetable)
