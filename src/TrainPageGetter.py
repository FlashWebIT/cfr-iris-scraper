from viewstate import ViewState
from src import config
import requests_html
from datetime import datetime, timedelta
from pprint import pprint

base_url = "https://appiris.infofer.ro/MyTrainRO.aspx?tren={}"

def get_station_ID_by_name(name):
    for x in config.global_station_list:
        if x["name"] == name:
            return x["station_id"]
            break
    else:
        return None

def extract_viewstate(reply):
    state = reply.html.find('#__VIEWSTATE', first=True)

    if not state:
        raise Exception("__VIEWSTATE element not present on webpage")

    state_value = state.attrs['value']

    return state_value

def state_decoder(state):
    last_timestamp_arrival=0
    last_timestamp_departure=0

    main_page = state[0][1][1][1][1][3][1][1][1]
    departure_date = main_page[13][0][0][0][7]

    # Collect the info box details
    info_box = main_page[13][1][1][1]
    info_box_data = {
        'rank': info_box[3][1][1][0][0][1],
        'train_id': info_box[5][1][1][0][0][1],
        'operator': info_box[7][1][1][0][0][1],
        'route': info_box[9][1][1][0][0][1],
        'status': info_box[11][1][1][0][0][1],
        'latest_information': {
        	'station': {
        		'name': info_box[13][1][1][0][0][1].split("[")[0].strip(),
        		'id': get_station_ID_by_name(info_box[13][1][1][0][0][1].split("[")[0].strip())
        	},
        	'status': info_box[13][1][1][0][0][1].split("[")[1].strip()[:-1] if ('[' in info_box[13][1][1][0][0][1]) else info_box[13][1][1][0][0][1],
        	'time': None if (info_box[15][1][1][0][0][1]=='' or info_box[15][1][1][0][0][1]=='&nbsp;') else int(datetime.timestamp(datetime.strptime(info_box[15][1][1][0][0][1],'%d.%m.%Y %H:%M')))
        },
        'delay': None if info_box[17][1][1][0][0][1]=='' else int(info_box[17][1][1][0][0][1]),
        'destination': info_box[19][1][1][0][0][1],
        'arrival_time': info_box[21][1][1][0][0][1],
        'next_stop': {
        	'station': { 
        		'name': info_box[23][1][1][0][0][1].strip(),
        		'id': get_station_ID_by_name(info_box[23][1][1][0][0][1].strip())
        	},
        	'time': None if (info_box[25][1][1][0][0][1]=='' or info_box[25][1][1][0][0][1]=='&nbsp;') else int(datetime.timestamp(datetime.strptime(info_box[25][1][1][0][0][1],'%d.%m.%Y %H:%M')))
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
        for entry_number in range(1, int(len(route_info_box) / 2)):
            entry = route_info_box[2 * entry_number - 1][1]

            if(entry[5][0][0][1]!=' ' and entry[5][0][0][1]!='&nbsp;'):
                temp_date = departure_date.split(' ')[2] + ' ' + entry[5][0][0][1]
                tscalc = datetime.timestamp(datetime.strptime(temp_date,'%d.%m.%Y %H:%M'))
                temp_date = datetime.strptime(temp_date,'%d.%m.%Y %H:%M')
                if(last_timestamp_arrival==0):
                    last_timestamp_arrival=tscalc
                else: 
                	if(last_timestamp_arrival>tscalc):
                		temp_date = temp_date + timedelta(days=1)
                last_timestamp_arrival=datetime.timestamp(temp_date)
                arrival_timestamp = int(datetime.timestamp(temp_date))
            else:
            	arrival_timestamp = None

            if(entry[9][0][0][1]!=' ' and entry[9][0][0][1]!='&nbsp;'):
                temp_date = departure_date.split(' ')[2] + ' ' + entry[9][0][0][1]
                tscalc = datetime.timestamp(datetime.strptime(temp_date,'%d.%m.%Y %H:%M'))
                temp_date = datetime.strptime(temp_date,'%d.%m.%Y %H:%M')
                if(last_timestamp_departure==0):
                    last_timestamp_departure=tscalc
                else: 
                	if(last_timestamp_departure>tscalc):
                		temp_date = temp_date + timedelta(days=1)
                last_timestamp_departure=datetime.timestamp(temp_date)
                departure_timestamp = int(datetime.timestamp(temp_date))
            else:
            	departure_timestamp = None

            entry_data = {
                'milepost': None if entry[1][0][0][1]=='' else int(entry[1][0][0][1]),
                'station': {
                	'name': entry[3][0][0][1].strip(),
                	'id': get_station_ID_by_name(entry[3][0][0][1].strip()),
                },
                'arrival_time': arrival_timestamp,
                'stop_duration': None if (entry[7][0][0][1]=='' or entry[7][0][0][1]=='&nbsp;') else int(entry[7][0][0][1]),
                'departure_time': departure_timestamp,
                'is_real_time': True if entry[11][0][0][1]=='Real' else False,
                'delay': 0 if (entry[13][0][0][1]=='' or entry[13][0][0][1]=='&nbsp;') else int(entry[13][0][0][1]),
                'mentions': None if (entry[15][0][0][1]=='' or entry[15][0][0][1]=='&nbsp;') else entry[15][0][0][1],
            }

            try:
                entry_data['mentions_extra'] = entry[15][0][1][1]
            except TypeError:
                entry_data['mentions_extra'] = None

            route_data.append(entry_data)

    return {
        'departure_date': departure_date.split(' ')[2],
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
