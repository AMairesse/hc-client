from hc_sensor import Sensor
import time
import base64

class Zigbee_sensor(Sensor):
    # Public attribute
    addr = None
    zb_link = None
    gpio = None
    
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(Zigbee_sensor, self).__init__(**kwargs)
        return

    def register(self, payload = {}):
        payload.update({'address': base64.b64encode(self.addr), 'gpio': self.gpio})
        super(Zigbee_sensor, self).register(payload)
        return

    # Update specific data
    def update_config_local(self, data):
        # Mandatory parameters
        try:
            self.gpio = int(data[u'gpio'])
            self.addr = base64.b64decode(data[u'address'])
        except:
            # if there is an error then deactivate the component
            self.gpio = None
            self.addr = None
        super(Zigbee_sensor, self).update_config_local(data)
        return

    # Convert the value from the zigbee to a temperature in celsius
    def convert_temperature(self, value):
        voltage = (value * 1200) / 1023
        temperature = round((voltage - 500) / 10.0, 3)
        return temperature


    # Read a sensor value and update data within the object
    def update(self):
        if (self.zb_link != None):
            # Send a immediate sample (IS) message to this one
            response = self.zb_link.send(self.addr, b'IS', None, b'4')
            # Read responses
            if (response == False):
                return False
            else:
                try:
                    parameters = response['parameter']
                    gpio_str = 'adc-' + str(self.gpio)
                    value = parameters[0][gpio_str]
                    temperature = self.convert_temperature(value)
                except:
                    return False
            # Update the value
            self.last_value = temperature
        # Component class update's method
        return super(Zigbee_sensor, self).update()
