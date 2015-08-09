from hc_component import Component
import time
import base64

class enOcean(Component):
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(enOcean, self).__init__(**kwargs)
        return

    # Update specific data
    def update_config_local(self, data):
        return

    # send a command
    def send(self, command, parameter, frame_id):
        # No send capacity for now
        return True
