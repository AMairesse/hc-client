from hc_heater import Heater, ACTIVE_LOW, ACTIVE_HIGH

class GPIO_heater(Heater):
    # Public attribute
    gpio = None

    def initialize(self):
        if self.gpio is None:
            # deactivate the heater
            self.status = False
            return False
        else:
            try:
                import RPi.GPIO as GPIO
            except :
                self.status = False
                return False
        super(GPIO_heater, self).initialize()
        return

    # Set heating system to on or off
    def set_heater(self, state):
        if self.gpio is not None:
            if self.mode == ACTIVE_LOW:
                # Heater is on 'active low' which mean than GND wil set it 'on'
                # We need to set it to "not(state)"
                GPIO.output(self.gpio, not(state))
            elif self.mode == ACTIVE_HIGH:
                # Heater is on 'active high' so we set directly to 'state'
                GPIO.output(self.gpio, state)
            else:
                print("WARNING - Heater : ", self.name, " is of an unknown mode : ", self.mode)
        super(GPIO_heater, self).set_heater(state)
        return

    # Update specific data
    def update_config_local(self, data):
        # Mandatory parameters
        try:
            self.gpio = int(data['gpio'])
        except:
            # if there is an error then deactivate the component
            self.gpio = None
        super(GPIO_heater, self).update_config_local(data)
        return
