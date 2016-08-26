import pytz
import datetime

# statics
UNKNOWN_TYPE = 'Unknown'
DEFAULT_FREQ = 0  # No automatic update by default
DEFAULT_TIMEZONE = 'UTC'
DEFAULT_STATUS = False


class Component(dict):
    # Private attributes
    client_hostname = None
    server_host = None
    server_user = None
    server_password = None
    # Public attributes
    component_type = UNKNOWN_TYPE
    type = UNKNOWN_TYPE
    url = None
    hostname = None
    name = None
    freq = DEFAULT_FREQ
    status = DEFAULT_STATUS
    last_value = None
    last_value_dt = None
    timezone = None
            
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(Component, self).__init__(**kwargs)
        self.__dict__ = self
        self.timezone = pytz.timezone(DEFAULT_TIMEZONE)
    
    # Read a component next refresh date
    def refresh_dt(self):
        if self.last_value_dt is None:
            return datetime.datetime.now(self.timezone)
        else:
            new_value_dt = self.last_value_dt + datetime.timedelta(seconds=self.freq)
            return max(new_value_dt, datetime.datetime.now(self.timezone))

    # Add a server hosting config
    def add_config_server(self, client_hostname, server_host, server_user, server_password):
        self.client_hostname = client_hostname
        self.server_host = server_host
        self.server_user = server_user
        self.server_password = server_password

    # Configure the component
    @staticmethod
    def initialize():
        return True
        
    # Register a new component on the server
    def register(self):
        return True

    # Update the component
    def update(self):
        self.last_value_dt = datetime.datetime.now(self.timezone)
        return True
