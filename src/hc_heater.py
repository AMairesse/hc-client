import dateutil.parser
import requests, json
from hc_zigbee import Zigbee
import base64

# statics
DEFAULT_MODE = "Low"
DEFAULT_HYSTERESIS = 0
ACTIVE_LOW = "Low"
ACTIVE_HIGH = "High"
TYPE_ZIGBEE = "ZigBee"
TYPE_GPIO = "GPIO"
HEATERS_PATH = '/api/heaters'
HEATERS_HISTORY_PATH = '/api/heaters_history'

class Heater(Zigbee):
    # Public attribute
    mode = None

    def initialize(self):
        # Initialize heater's
        if ((self.type == TYPE_GPIO) and (self.gpio != None)):
            try:
                import RPi.GPIO as GPIO
            except :
                self.status = False
                return False
            if (self.mode == ACTIVE_LOW):
                # Heater is on 'active low' which mean than GND wil set it 'on'
                # We need to set it to 'True' for starting
                GPIO.setup(self.gpio, GPIO.OUT, initial=True)
            elif (self.mode == ACTIVE_HIGH):
                # Heater is on 'active high' so we set it to False
                GPIO.setup(self.gpio, GPIO.OUT, initial=False)
            else:
                print ("WARNING - Heater : ", self.name, " is of an unknown mode : ", self.mode)
        elif ((self.type == TYPE_ZIGBEE) and (self.gpio != None)):
            # Default to off
            self.set_heater(False)
        else:
            # Ultimatly deactivate the heater
            self.status = False
        return True

    # Register a new heater on the server
    def register(self):
        payload = {'hostname': self.client_hostname, 'type': self.type, 'mode': DEFAULT_MODE, 'name': self.name.decode('utf_8'), 'address': base64.b64encode(self.addr), 'freq': self.freq, 'hysteresis': DEFAULT_HYSTERESIS, 'status' : self.status}
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
        if ((self.type == TYPE_GPIO) and (self.gpio != None)):
            if (self.mode == ACTIVE_LOW):
                # Heater is on 'active low' which mean than GND wil set it 'on'
                # We need to set it to "not(state)"
                GPIO.output(self.gpio, not(state))
            elif (self.mode == ACTIVE_HIGH):
                # Heater is on 'active high' so we set directly to 'state'
                GPIO.output(self.gpio, state)
            else:
                print ("WARNING - Heater : ", self.name, " is of an unknown mode : ", self.mode)
        elif ((self.type == TYPE_ZIGBEE) and (self.zb_link.zb != None) and (self.gpio != None)):
            if ((self.mode == ACTIVE_LOW) and not(state)):
                # Heater is on 'active low' which mean than GND wil set it 'on'
                # Wanted state is OFF so we send a \x05 parameter "Digital output, high"
                param = b'\x05'
            elif ((self.mode == ACTIVE_HIGH) and state):
                # Heater is on 'active high' which mean than GND wil set it 'off'
                # Wanted state is ON so we send a \x05 parameter "Digital output, high"
                param = b'\x05'
            else:
                # In all other cases we send a \x04 parameter "Digital output, low"
                param = b'\x04'
            # Send a Dx config ('x' being the used gpio) message with the parameter
            gpio_str = 'D' + str(self.gpio)
            response = self.send(gpio_str.encode("utf_8"), param, b'5')
            # Read responses
            if (response == False):
                return False
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
        super(Heater, self).update_config_local(data)
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
