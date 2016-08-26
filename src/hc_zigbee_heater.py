from hc_heater import Heater, ACTIVE_LOW, ACTIVE_HIGH
import base64

class Zigbee_heater(Heater):
    # Public attribute
    addr = None
    zb_link = None
    gpio = None

    def initialize(self):
        # Initialize heater's
        if self.gpio is None:
            # deactivate the heater
            self.status = False
            return False
        super(Zigbee_heater, self).initialize()
        return

    def register(self, payload = {}):
        payload.update({'address': base64.b64encode(self.addr)})
        super(Zigbee_heater, self).register(payload)
        return

    # Set heating system to on or off
    def set_heater(self, state):
        if (self.zb_link.zb is not None) and (self.gpio is not None):
            if (self.mode == ACTIVE_LOW) and not state:
                # Heater is on 'active low' which mean than GND wil set it 'on'
                # Wanted state is OFF so we send a \x05 parameter "Digital output, high"
                param = b'\x05'
            elif (self.mode == ACTIVE_HIGH) and state:
                # Heater is on 'active high' which mean than GND wil set it 'off'
                # Wanted state is ON so we send a \x05 parameter "Digital output, high"
                param = b'\x05'
            else:
                # In all other cases we send a \x04 parameter "Digital output, low"
                param = b'\x04'
            # Send a Dx config ('x' being the used gpio) message with the parameter
            gpio_str = 'D' + str(self.gpio)
            response = self.zb_link.send(self.addr, gpio_str.encode("utf_8"), param, b'5')
            # Read responses
            if response is False:
                return False
        super(Zigbee_heater, self).set_heater(state)
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
        super(Zigbee_heater, self).update_config_local(data)
        return

