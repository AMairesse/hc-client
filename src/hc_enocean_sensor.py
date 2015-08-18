from hc_sensor import Sensor

class enOcean_sensor(Sensor):
    # Public attribute
    addr = None
    rorg = None
    rorg_func = None
    rorg_type = None
    
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(enOcean_sensor, self).__init__(**kwargs)
        return

    def register(self, payload = {}):
        payload.update({'address': self.addr, 'rorg': self.rorg, 'rorg_func': self.rorg_func, 'rorg_type': self.rorg_type})
        super(enOcean_sensor, self).register(payload)
        return

    # Update specific data
    def update_config_local(self, data):
        # Mandatory parameters
        try:
            self.addr = int(data[u'address'])
            self.rorg = int(data[u'rorg'])
            self.rorg_func = int(data[u'rorg_func'])
            self.rorg_type = int(data[u'rorg_type'])
        except:
            # if there is an error then deactivate the component
            self.addr = None
            self.rorg = None
            self.rorg_func = None
            self.rorg_type = None
        super(enOcean_sensor, self).update_config_local(data)
        return

