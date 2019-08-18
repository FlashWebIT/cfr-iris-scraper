from viewstate import ViewState
from src import config
import requests_html
from datetime import datetime, timedelta
import re

base_url = "https://appiris.infofer.ro/MyTrainRO.aspx?tren={}"


def get_station_id_by_name(name):
    if name in config.global_station_list:
        return config.global_station_list[name]

    return None


def extract_viewstate(reply):
    state = reply.html.find('#__VIEWSTATE', first=True)

    if not state:
        raise Exception("__VIEWSTATE element not present on webpage")

    state_value = state.attrs['value']

    return state_value


def state_decoder(state):
    main_page = state[0][1][1][1][1][3][1][1][1]

    departure_date_raw = main_page[13][0][0][0][7]
    departure_date = re.findall(r"(\d+.\d+.\d+)", departure_date_raw)[0]

    # Collect the info box details
    info_box = main_page[13][1][1][1]

    # Process the latest info field
    latest_info_raw = info_box[13][1][1][0][0][1]
    info_station, info_status = re.findall(r"(.*?) \[(.*?)\]", latest_info_raw)[0]
    info_station = info_station.strip()

    # Process the last update time
    info_time_raw = info_box[15][1][1][0][0][1]
    info_time = None
    if info_time_raw and info_time_raw != '&nbsp;':
        info_time = datetime.timestamp(datetime.strptime(info_time_raw, '%d.%m.%Y %H:%M'))

    # Process the delay field
    delay_raw = info_box[17][1][1][0][0][1]
    delay = None
    if delay_raw != '':
        delay = int(delay_raw)

    # Process the next stop information
    next_station_raw = info_box[23][1][1][0][0][1]
    next_station = next_station_raw.strip()

    # Process the next stop time
    next_stop_time_raw = info_box[25][1][1][0][0][1]
    next_stop_time = None
    if next_stop_time_raw and next_stop_time_raw != '&nbsp;':
        next_stop_time = datetime.timestamp(datetime.strptime(next_stop_time_raw, '%d.%m.%Y %H:%M'))

    # Other information
    destination_station = info_box[19][1][1][0][0][1]

    destination_arrival_time_raw = info_box[21][1][1][0][0][1]
    destination_arrival_time = None
    if destination_arrival_time_raw and destination_arrival_time_raw != '&nbsp;':
        destination_arrival_time = datetime.timestamp(datetime.strptime(destination_arrival_time_raw, '%d.%m.%Y %H:%M'))       

    # Build the data dict
    info_box_data = {
        'rank': info_box[3][1][1][0][0][1],
        'train_id': info_box[5][1][1][0][0][1],
        'operator': info_box[7][1][1][0][0][1],
        'route': info_box[9][1][1][0][0][1],
        'status': info_box[11][1][1][0][0][1],
        'latest_information': {
            'station': {
                'name': info_station,
                'id': get_station_id_by_name(info_station),
            },
            'status': info_status,
            'time': int(info_time) if info_time else None,
        },
        'delay': delay,
        'destination': {
            'station': {
                'name': destination_station,
                'id': get_station_id_by_name(destination_station)
            },
            'arrival_time': int(destination_arrival_time) if destination_arrival_time else None
        },
        'next_stop': {
            'station': {
                'name': next_station,
                'id': get_station_id_by_name(next_station),
            },
            'time': int(next_stop_time) if next_stop_time else None,
        },
        'distance': info_box[27][1][1][0][0][1][:-1],
        'trip_duration': info_box[29][1][1][0][0][1][:-1],
        'average_speed': info_box[31][1][1][0][0][1][:-1],
    }

    # Collect the route info box data, if available
    # Note: The route info is not displayed for canceled trains,
    # yet it is available in the state information, albeit at a different place
    # in the structure

    route_data = []
    route_info_box = None

    # Find the route info box
    try:
        route_info_box = main_page[17][1][1][1]
    except TypeError:
        try:
            # The route info box is usually found here on cancelled trains
            route_info_box = main_page[15][1][1][1]
        except TypeError:
            pass

    if route_info_box:
        last_arrival_timestamp = 0
        last_departure_timestamp = 0

        for entry_number in range(1, int(len(route_info_box) / 2)):
            entry = route_info_box[2 * entry_number - 1][1]

            # Compute the arrival timestamp for this station
            arrival_time_raw = entry[5][0][0][1]
            arrival_timestamp = None

            if arrival_time_raw and arrival_time_raw != '&nbsp;':
                # We assume the train arrives at this station on the same day it left
                arrival_time_assumption = datetime.strptime(departure_date + ' ' + arrival_time_raw, '%d.%m.%Y %H:%M')

                if last_arrival_timestamp and last_arrival_timestamp > datetime.timestamp(arrival_time_assumption):
                    # We were wrong in our assumption and the train actually arrives
                    # on the next day at this station, hence we must add one day to the arrival time
                    arrival_time_assumption = arrival_time_assumption + timedelta(days=1)

                last_arrival_timestamp = datetime.timestamp(arrival_time_assumption)
                arrival_timestamp = int(last_arrival_timestamp)

            # Compute the departure timestamp for this station
            departure_time_raw = entry[9][0][0][1]
            departure_timestamp = None

            if departure_time_raw and departure_time_raw != '&nbsp;':
                # We assume the train departs from this station on the same day it left
                departure_time_assumption = datetime.strptime(departure_date + ' ' + departure_time_raw, '%d.%m.%Y %H:%M')

                if last_departure_timestamp and last_departure_timestamp > datetime.timestamp(departure_time_assumption):
                    # We were wrong in our assumption and the train actually departs
                    # on the next day from this station, hence we must add one day to the departure time
                    departure_time_assumption = departure_time_assumption + timedelta(days=1)

                last_departure_timestamp = datetime.timestamp(departure_time_assumption)
                departure_timestamp = int(last_departure_timestamp)

            # Decode other raw data
            milepost_raw = entry[1][0][0][1]
            milepost = None
            if milepost_raw:
                milepost = int(milepost_raw)

            station = entry[3][0][0][1].strip()

            stop_duration_raw = entry[7][0][0][1]
            stop_duration = None
            if stop_duration_raw and stop_duration_raw != "&nbsp;":
                stop_duration = int(stop_duration_raw)

            delay_raw = entry[13][0][0][1]
            delay = 0
            if delay_raw and delay_raw != "&nbsp;":
                delay = int(delay_raw)

            mentions_raw = entry[15][0][0][1]
            mentions = None
            if mentions_raw and mentions_raw != "&nbsp;":
                mentions = mentions_raw

            entry_data = {
                'milepost': milepost,
                'station': {
                    'name': station,
                    'id': get_station_id_by_name(station),
                },
                'arrival_time': arrival_timestamp,
                'stop_duration': stop_duration,
                'departure_time': departure_timestamp,
                'is_real_time': entry[11][0][0][1] == 'Real',
                'delay': delay,
                'mentions': mentions,
            }

            try:
                entry_data['mentions_extra'] = entry[15][0][1][1]
            except TypeError:
                entry_data['mentions_extra'] = None

            route_data.append(entry_data)

    return {
        'departure_date': departure_date,
        'info_box': info_box_data,
        'route_data': route_data,
    }


def get_train(train_id):
    session = requests_html.HTMLSession()

    # Get the initial page and retrieve its __VIEWSTATE
    reply = session.get(base_url.format(train_id))
    state_value = extract_viewstate(reply)
    vs = ViewState(state_value)
    state = vs.decode()

    # Check whether the train actually exists
    if state[0][1][1][1][1][3][1][1][1][11][0][0][1] != '':
        raise Exception("Train not found")

    trips = []

    # Decode the current page and append it to the trips array
    current_trip = state_decoder(state)
    trips.append(current_trip)

    # Check whether the train is single-page or multi-page
    if state[1]['DetailsView1'][0][6] == 1:
        print("Single-page train")
    else:
        print("Multi-page train!")

        # Switch the page
        reply = session.post(base_url.format(train_id), data={
            '__EVENTTARGET': 'DetailsView1',
            '__EVENTARGUMENT': 'Page$2',
            '__VIEWSTATE': state_value,
            '__VIEWSTATEGENERATOR': '86BE64DB',
            'TextTrnNo': str(train_id),
        })

        state_value = extract_viewstate(reply)
        vs = ViewState(state_value)
        state = vs.decode()

        # Decode the current page and append it to the trips array
        current_trip = state_decoder(state)
        trips.append(current_trip)

    return trips
