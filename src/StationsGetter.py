from viewstate import ViewState
import requests_html
from pprint import pprint

base_url = "https://appiris.infofer.ro/SosPlcRO.aspx"


def extract_viewstate(reply):
    state = reply.html.find('#__VIEWSTATE', first=True)

    if not state:
        raise Exception("__VIEWSTATE element not present on webpage")

    state_value = state.attrs['value']

    return state_value


def state_decoder(state):
    station_list = state[0][1][1][1][1][3][1][1][1][5][0][1]

    # Rebuild the station information
    stations = []
    for i in range(0, len(station_list[0]) - 1):
        stations.append({
            'station_id': int(station_list[1][i]),
            'name': station_list[0][i].strip(),
        })

    stations.sort(key=lambda element: element['station_id'])

    return stations


def get_stations():
    session = requests_html.HTMLSession()

    # Get the initial page and retrieve its __VIEWSTATE
    reply = session.get(base_url)
    state_value = extract_viewstate(reply)
    vs = ViewState(state_value)
    state = vs.decode()

    stations = state_decoder(state)

    return stations
