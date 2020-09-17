from viewstate import ViewState
import requests_html
from datetime import datetime
from dateutil import tz


base_url = "https://appiris.infofer.ro/SosPlcRO.aspx"


def extract_states(reply):
    state = reply.html.find('#__VIEWSTATE', first=True)

    if not state:
        raise Exception("__VIEWSTATE element not present on webpage")

    event_validation = reply.html.find('#__EVENTVALIDATION', first=True)

    if not event_validation:
        raise Exception("__EVENTVALIDATION element not present on webpage")

    state_value = state.attrs['value']
    event_validation_value = event_validation.attrs['value']

    return state_value, event_validation_value


def state_decoder(state):
    train_list = state[0][1][1][1][1][3][1][1][1][19][1][1][1]

    trains = []
    for i in range(1, int(len(train_list) / 2)):
        train = train_list[2 * i - 1][1]
        train_data = {
            'rank': train[1][0][0][1],
            'train_id': train[3][0][0][1],
            'operator': train[5][0][0][1].strip(),
            'origin': train[7][0][0][1].strip().replace('&nbsp;', ''),
            'delay': train[9][0][0][1].replace('&nbsp;', ''),
            'arrival_time': train[11][0][0][1].replace('&nbsp;', ''),
            'departure_time': train[13][0][0][1].replace('&nbsp;', ''),
            'arrival_timestamp': None,
            'departure_timestamp': None,
            'destination': train[15][0][0][1].strip().replace('&nbsp;', ''),
            'platform': train[17][0][0][1].strip().replace('&nbsp;', ''),
            'is_origin': train[19][0][0][1] == 'O',
            'is_destination': train[19][0][0][1] == 'D',
            'is_stop': train[19][0][0][1] == 'S',
            'mentions': train[21][0][0][1].strip().replace('&nbsp;', ''),
        }

        # Sanitize the data
        if not train_data['delay']:
            train_data['delay'] = 0
        else:
            train_data['delay'] = int(train_data['delay'])

        if not train_data['arrival_time']:
            train_data['arrival_time'] = None

        if not train_data['departure_time']:
            train_data['departure_time'] = None

        if not train_data['origin']:
            train_data['origin'] = None

        if not train_data['destination']:
            train_data['destination'] = None

        if not train_data['platform']:
            train_data['platform'] = None

        if not train_data['mentions']:
            train_data['mentions'] = None

        # Add any required timestamps
        timezone = tz.gettz('Europe/Bucharest')
        today = datetime.combine(datetime.now(tz=timezone), datetime.min.time())

        if train_data['arrival_time']:
            arrival_time = datetime.strptime(train_data['arrival_time'], '%H:%M').time()
            train_data['arrival_timestamp'] = datetime.combine(today, arrival_time, timezone).isoformat()

        if train_data['departure_time']:
            arrival_time = datetime.strptime(train_data['departure_time'], '%H:%M').time()
            train_data['departure_timestamp'] = datetime.combine(today, arrival_time, timezone).isoformat()

        trains.append(train_data)

    return trains


def get_timetable(station_id):
    session = requests_html.HTMLSession()

    # Get the initial page
    reply = session.get(base_url)
    state_value, event_validation_value = extract_states(reply)

    # Verify the station ID
    vs = ViewState(state_value)
    state = vs.decode()
    station_id_list = state[0][1][1][1][1][3][1][1][1][5][0][1][1]
    if not str(station_id) in station_id_list:
        raise Exception('Invalid Station ID!')

    # Select the station dropdown
    reply = session.post(base_url, data={
        'ScriptManager1': 'UpdatePanel1|DropStPlc',
        '__EVENTTARGET': 'DropStPlc',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': state_value,
        '__VIEWSTATEGENERATOR': 'EF6047A0',
        '__EVENTVALIDATION': event_validation_value,
        'DropStPlc': str(station_id),
        'RadioButtonSetStatii': '0',
        '__ASYNCPOST': 'false',
    })
    state_value, event_validation_value = extract_states(reply)

    # Get the button's text
    button = reply.html.find('#Button2', first=True)

    if not button:
        raise Exception("Button2 element not present on webpage")

    button_value = button.attrs['value']

    # Press the button
    reply = session.post(base_url, data={
        'ScriptManager1': 'UpdatePanel1|Button2',
        'DropStPlc': str(station_id),
        'RadioButtonSetStatii': '0',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': state_value,
        '__VIEWSTATEGENERATOR': 'EF6047A0',
        '__EVENTVALIDATION': event_validation_value,
        '__ASYNCPOST': 'false',
        'Button2': button_value,
    })
    state_value, event_validation_value = extract_states(reply)

    # Press the "view more" button
    reply = session.post(base_url, data={
        'ScriptManager1': 'UpdatePanel1|Button3',
        'DropStPlc': str(station_id),
        'RadioButtonList1': 'Toate trenurile',
        'RadioButtonSetStatii': '0',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': state_value,
        '__VIEWSTATEGENERATOR': 'EF6047A0',
        '__EVENTVALIDATION': event_validation_value,
        '__ASYNCPOST': 'false',
        'Button3': 'Mai mult...',
    })
    state_value, event_validation_value = extract_states(reply)

    vs = ViewState(state_value)
    state = vs.decode()

    timetable = state_decoder(state)

    return timetable
