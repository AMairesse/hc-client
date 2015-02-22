from hc_component import Component
import time
import base64

class Zigbee(Component):
    # Public attribute
    addr = None
    zb_link = None
    gpio = None
    
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(Zigbee, self).__init__(**kwargs)
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
        return

    # send a command
    def send(self, command, parameter, frame_id):
        if (parameter == None):
            self.zb_link.zb.send('remote_at', command=command, dest_addr_long = self.addr, frame_id = frame_id)
        else:
            self.zb_link.zb.send('remote_at', command=command, parameter=parameter, dest_addr_long = self.addr, frame_id = frame_id)
        nb_try = 4
        # Read responses
        while (nb_try > 0):
            if (self.zb_link.packets.qsize() > 0):
                data = self.zb_link.packets.get_nowait()
                # do not care of other packets
                if ((data['command'] != command) or (data['frame_id'] != frame_id)):
                    continue
                if (data['status'] != b'\x00'):
                    return False
                else:
                    return data
            else:
                time.sleep(1)
                nb_try = nb_try - 1
        return False
