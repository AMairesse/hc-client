import dateutil.parser
import requests, json
from hc_component import Component
import glob, os
import base64

# statics
SENSORS_PATH = '/api/sensors'
TEMPERATURES_PATH = '/api/temperatures'
DEFAULT_ROOM = 'Unknown'

class Sensor(Component):
    # Public attribute
    offset = 0.0
    room_name = DEFAULT_ROOM
            
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(Sensor, self).__init__(**kwargs)
        return
    
    # Register a new sensor on the server
    def register(self, payload = {}):
        payload.update({'hostname': self.client_hostname, 'name': self.name.decode('utf_8'), 'type': self.type, 'freq': self.freq, 'room_name': self.room_name, 'status' : self.status})
        requested_url = self.server_host + SENSORS_PATH + '/'
        if (self.server_user == None):
            r = requests.post(requested_url, data=payload)
        else:
            r = requests.post(requested_url, auth=(self.server_user, self.server_password), data=payload)
        text_response = json.loads(r.text)
        try:
            self.url = str(text_response[u'id'])
        except:
            # If server registration failed then do nothing more
            return
        super(Sensor, self).register()
        return

    # Update specific data
    def update_config_local(self, data):
        # Those data are optionnal
        try:
            self.last_value = float(data[u'last_temperature'][u'temp'])
            self.last_value_dt = dateutil.parser.parse(str(data[u'last_temperature'][u'date']))
        except:
            self.last_value = None
            self.last_value_dt = None
        return

    # Upload last data to a webserver
    def upload(self):
        # Upload last data read
        payload = {'sensor': self.url, 'date': self.last_value_dt.isoformat(), 'temp': self.last_value}
        requested_url = self.server_host + TEMPERATURES_PATH + '/'
        if (self.server_user == None):
            r = requests.post(requested_url, data=payload)
        else:
            r = requests.post(requested_url, auth=(self.server_user, self.server_password), data=payload)
        if (r.status_code != 201):
            print("Error during communication with the server. Response : ", r, " - Requested url : ", requested_url, " - Payload : ", payload)
        return
