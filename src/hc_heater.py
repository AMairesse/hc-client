import dateutil.parser
import requests, json
from hc_component import Component

# statics
DEFAULT_MODE = "Low"
DEFAULT_HYSTERESIS = 0
ACTIVE_LOW = "Low"
ACTIVE_HIGH = "High"
HEATERS_PATH = '/api/heaters'
HEATERS_HISTORY_PATH = '/api/heaters_history'

class Heater(Component):
    # Public attribute
    mode = None

    def initialize(self):
        # Initialize heater's
        self.set_heater(False)
        return True

    # Register a new heater on the server
    def register(self, payload = {}):
        payload.update({'hostname': self.client_hostname, 'type': self.type, 'mode': DEFAULT_MODE, 'name': self.name.decode('utf_8'), 'freq': self.freq, 'hysteresis': DEFAULT_HYSTERESIS, 'status' : self.status})
        requested_url = self.server_host + HEATERS_PATH + '/'
        if (self.server_user == None):
            r = requests.post(requested_url, data=payload)
        else:
            r = requests.post(requested_url, auth=(self.server_user, self.server_password), data=payload)
        text_response = json.loads(r.text)
        self.url = str(text_response[u'id'])
        super(Heater, self).register()
        return

    # Read a heater state and update data within the object
    def update(self):
        # Read from server
        if (self.server_user == None):
            r = requests.get(self.url)
        else:
            r = requests.get(self.url, auth=(self.server_user, self.server_password))
        try:
            text_response = json.loads(r.text)
            new_value = bool(text_response[u'state'])
        except:
            # Super class update's method
            super(Heater, self).update()
            return False
        # If state has not changed then no update to upload
        if (self.last_value == new_value):
            updated = False
        else:
            updated = True
        # Set the heater to the new state
        self.last_value = new_value
        self.set_heater(new_value)
        # Super class update's method
        super(Heater, self).update()
        return updated

    # Set heating system to on or off
    def set_heater(self, state):
        # This method must be overriden is sub-class
        return

    # Update specific data
    def update_config_local(self, data):
        # Mandatory parameters
        try:
            self.mode = str(data[u'mode'])
        except:
            # if there is an error then deactivate the component
            self.mode = None
        # Those data are optionnal
        try:
            self.last_value = bool(data[u'last_history'][u'state'])
            self.last_value_dt = dateutil.parser.parse(str(data[u'last_history'][u'date']))
        except:
            self.last_value = None
            self.last_value_dt = None
        return

    # Upload last data to a webserver
    def upload(self):
        # Upload last data read
        payload = {'heater': self.url, 'date': self.last_value_dt.isoformat(), 'state': self.last_value}
        requested_url = self.server_host + HEATERS_HISTORY_PATH + '/'
        if (self.server_user == None):
            r = requests.post(requested_url, data=payload)
        else:
            r = requests.post(requested_url, auth=(self.server_user, self.server_password), data=payload)
        return
