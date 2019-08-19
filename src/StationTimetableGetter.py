from viewstate import ViewState
import requests_html
from pprint import pprint

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
            'operator': train[5][0][0][1],
            'origin': train[7][0][0][1],
            'delay': 0 if train[9][0][0][1]=='&nbsp;' else int(train[9][0][0][1]),
            'arrival_time': train[11][0][0][1],
            'departure_time': train[13][0][0][1],
            'destination': train[15][0][0][1],
            'platform': train[17][0][0][1] if train[17][0][0][1]!='&nbsp;' else None,
            'is_origin': train[19][0][0][1] == 'O',
            'is_destination': train[19][0][0][1] == 'D',
            'is_stop': train[19][0][0][1] == 'S',
            'mentions': train[21][0][0][1],
        }
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
