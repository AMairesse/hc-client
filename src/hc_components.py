from hc_zigbee_heater import Zigbee_heater
from hc_zigbee_sensor import Zigbee_sensor
from hc_w1_sensor import W1_sensor, W1_BUS_DIRECTORY, W1_BUS_FILE
from hc_enocean_sensor import enOcean_sensor
from hc_heater import HEATERS_PATH
from hc_sensor import SENSORS_PATH
import glob
import os
import requests
import json
import pytz
import time
import datetime
import threading

# statics
W1_TYPE = 'W1'
ZIGBEE_TYPE = 'ZigBee'
ENOCEAN_TYPE = 'enOcean'
DEFAULT_ENOCEAN_NAME = 'Name has to be set'
DEFAULT_TIMEZONE = 'UTC'
HEATER_COMPONENT = 'Heater'
SENSOR_COMPONENT = 'Sensor'


class Components(threading.Thread):
    initialized = False

    def set_zb_link(self, zb_link):
        self.zb_link = zb_link
        return

    def set_enOcean_link(self, enOcean_link):
        self.enOcean_link = enOcean_link
        return

    def __init__(self):
        super(Components, self).__init__()
        self.client_hostname = None
        self.server_host = None
        self.server_user = None
        self.server_password = None
        self.timezone = pytz.timezone(DEFAULT_TIMEZONE)
        self.components_list = []
        self.stay_running = True
        self.zb_link = None
        self.enOcean_link = None
        return

    def __del__(self):
        # delete objects of the list
        for component in self.components_list:
            del component
        return

    def create_component(self, type, component_type, **kwargs):
        if (type == ZIGBEE_TYPE) and (component_type == HEATER_COMPONENT):
            component = Zigbee_heater(type=type, zb_link=self.zb_link, **kwargs)
            component.component_type = HEATER_COMPONENT
        elif (type == ZIGBEE_TYPE) and (component_type == SENSOR_COMPONENT):
            component = Zigbee_sensor(type=type, zb_link=self.zb_link, **kwargs)
            component.component_type = SENSOR_COMPONENT
        elif (type == W1_TYPE) and (component_type == SENSOR_COMPONENT):
            component = W1_sensor(type=type, **kwargs)
            component.component_type = SENSOR_COMPONENT
        elif (type == ENOCEAN_TYPE) and (component_type == SENSOR_COMPONENT):
            component = enOcean_sensor(type=type, **kwargs)
            component.component_type = SENSOR_COMPONENT
        else:
            return False
        return component

    def add_component(self, component):
        self.components_list.append(component)
        return

    def run(self):
        # Only run on components with a positive status and
        # a frequency different from 0
        running_list = []
        for component in self.components_list:
            if (component.status is True) & (component.freq != 0):
                running_list.append(component)
        # If there is nothing in the list then do nothing and leave
        if running_list is []:
            return
        # Otherwise keep updating...
        while self.stay_running:
            result = self.update_next(running_list)
            if result is False:
                break
        return

    def stop(self):
        self.stay_running = False
        while self.isAlive():
            time.sleep(0.1)
        return

    def detect(self):
        # Detect Zigbee components in the network
        # Send a Node Discover (ND) message to broadcast
        self.zb_link.broadcast(b'ND', b'1')
        # Detect W1 components on the host
        devicelist = glob.glob(W1_BUS_DIRECTORY + '28*')
        for device in devicelist:
            devicefile = device + W1_BUS_FILE
            if os.path.exists(devicefile):
                [_, component_name] = device.rsplit('/', 1)
                component = self.find_by_name_and_type(component_name, SENSOR_COMPONENT, W1_TYPE)
                if component is None:
                    new_w1_sensor = self.create_component(W1_TYPE, SENSOR_COMPONENT, name=component_name)
                    self.add_component(new_w1_sensor)
                    new_w1_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user,
                                                    self.server_password)
                    new_w1_sensor.register()
        return

    def initialize(self):
        # Configure all components, add config server
        self.update_config_by_type(ZIGBEE_TYPE, HEATER_COMPONENT, HEATERS_PATH)
        self.update_config_by_type(ZIGBEE_TYPE, SENSOR_COMPONENT, SENSORS_PATH)
        self.update_config_by_type(W1_TYPE, SENSOR_COMPONENT, SENSORS_PATH)
        self.update_config_by_type(ENOCEAN_TYPE, SENSOR_COMPONENT, SENSORS_PATH)
        self.initialized = True
        # Detect components availables
        self.detect()
        # Initialize components
        for component in self.components_list:
            # Only initialize components with a positive status
            if component.status is True:
                component.initialize()
        print(self.components_list)
        return

    # Add a server hosting config
    def add_config_server(self, client_hostname, server_host, server_user, server_password):
        self.client_hostname = client_hostname
        self.server_host = server_host
        self.server_user = server_user
        self.server_password = server_password
        # update components also if needed
        # (useful only for parameter change while running, when
        #  called the first time the components_list is empty)
        for component in self.components_list:
            component.add_config_server(client_hostname, server_host, server_user, server_password)
        return

    # Function to find by name and type
    def find_by_name_and_type(self, component_name, component_type, type):
        component = next((x for x in self.components_list if ((x.name == component_name) and
                                                              (x.component_type == component_type)
                                                              and (x.type == type))), None)
        return component

    # Function to find by addr (zigbee and enOcean only)
    def find_by_addr(self, addr):
        component = next((x for x in self.components_list if (((x.type == ZIGBEE_TYPE) or
                                                               (x.type == ENOCEAN_TYPE)) and
                                                              (x.addr == addr))), None)
        return component

    # Function to find by addr and gpio (zigbee only)
    def find_by_addr_and_gpio(self, addr, gpio):
        component = next((x for x in self.components_list if ((x.type == ZIGBEE_TYPE) and
                                                              (x.addr == addr) and (x.gpio == gpio))), None)
        return component

    # Function to sort by refresh_dt
    @staticmethod
    def sort_by_refresh_dt(item):
        return item.refresh_dt()

    # Read component from config server
    def update_config_by_type(self, component_class, component_type, PATH):
        # Request known components for this host from the server
        requested_url = self.server_host + PATH + '/'
        try:
            if self.server_user is None:
                r = requests.get(requested_url)
            else:
                r = requests.get(requested_url, auth=(self.server_user, self.server_password))
            text_response = json.loads(r.text)
            nb_result = len(text_response)
            results = text_response
        except:
            # If we don't manage to get anything then just get out
            print("Error while retrieving server's data")
            return
        # Process each result
        for i in range(nb_result):
            # Check if the component is already known
            component_name = str(results[i]['name']).encode('utf_8')
            component_type = str(results[i]['type'])
            if component_type is not component_class:
                # Listed component is not of the type/class we are looking for
                # go on with the next one
                continue
            component = self.find_by_name_and_type(component_name, component_type, component_type)
            if component is None:
                # New component, let's create it in the list
                component = self.create_component(component_class, component_type, name=component_name)
                self.add_component(component)
                # Add link to server
                component.add_config_server(self.client_hostname, self.server_host,
                                            self.server_user, self.server_password)
            # Update the component parameters
            component.status = bool(results[i]['status'])
            component.url = str(results[i]['id'])
            component.freq = int(results[i]['freq'])
            component.update_config_local(results[i])
        return

    # Find the next component to process, wait for it and proceed
    def update_next(self, running_list):
        # Sort list by refesh date
        running_list.sort(key=self.sort_by_refresh_dt)
        # Take the first one
        component = running_list[0]
        # Wait for that time to append
        next_refresh_dt = component.refresh_dt()
        time_before_wait = datetime.datetime.now(self.timezone)
        if time_before_wait < next_refresh_dt:
            delta = next_refresh_dt - time_before_wait
            tenth_of_seconds_to_wait = int(delta.total_seconds() * 10)
            for i in range(tenth_of_seconds_to_wait):
                time.sleep(0.1)
                if self.stay_running is False:
                    return
        # Update the component
        updated = component.update()
        # Upload data if a server is known
        if (updated is True) and (self.server_host is not None):
            component.upload()
        elif updated is False:
            # if update failed then update last_value_dt
            # to refresh_dt for next retry
            component.last_value_dt = component.refresh_dt()
        return

    # This is a call back function for the ZigBee network incoming messages
    def callback_ZB(self, data):
        print("incoming ZB data")
        # **** Automatic sample
        if data['id'] == 'rx_io_data_long_addr':
            # If we're not initialized yet, do nothing
            if self.initialized is False:
                return
            # Process each sample
            samples = data['samples']
            for sample in samples:
                for item in sample:
                    gpio = int(item[4:])
                    value = int(sample[item])
                    # Search the component
                    component = self.find_by_addr_and_gpio(data['source_addr_long'], gpio)
                    if component is None:
                        # New component, let's create it in the list
                        new_zb_sensor = self.create_component(ZIGBEE_TYPE, SENSOR_COMPONENT, name=None,
                                                              addr=data['source_addr_long'], gpio=gpio)
                        self.add_component(new_zb_sensor)
                        # Add link to server
                        new_zb_sensor.add_config_server(self.client_hostname, self.server_host,
                                                        self.server_user, self.server_password)
                        # Ask him for his name
                        self.zb_link.identify(new_zb_sensor.addr)
                    else:
                        if component.url is None:
                            # The component is not registered yet, ask him for his name
                            self.zb_link.identify(component.addr)
                        elif component.status is False:
                            # The component is desactivated, we should not save the data
                            return
                        else:
                            # The component is fully registered and active so upload the sample
                            try:
                                # Convert to Celsuis
                                temperature = component.convert_temperature(value)
                                # Update the value
                                component.last_value = temperature
                                component.last_value_dt = datetime.datetime.now(component.timezone)
                                # Send it to the server
                                component.upload()
                            except:
                                print("Error processing a sample (data : ", data, ")")
                                continue
        # **** Node discovery
        elif data['command'] == b'ND':
            # If we're not initialized yet, do nothing
            if self.initialized is False:
                return
            # Process answers to Node Discovery (ND) calls
            zb_id = data['parameter']['node_identifier']
            zb_addr = data['parameter']['source_addr_long']
            component = self.find_by_addr(zb_addr)
            # Update the name
            if component is None:
                # Not found ! Let's add it (sensor and heater)
                new_zb_sensor = self.create_component(ZIGBEE_TYPE, SENSOR_COMPONENT, name=zb_id, addr=zb_addr)
                self.add_component(new_zb_sensor)
                new_zb_heater = self.create_component(ZIGBEE_TYPE, HEATER_COMPONENT, name=zb_id, addr=zb_addr)
                self.add_component(new_zb_heater)
                # Add link to server
                new_zb_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user,
                                                self.server_password)
                new_zb_heater.add_config_server(self.client_hostname, self.server_host, self.server_user,
                                                self.server_password)
            else:
                component.name = zb_id
                # Register it to the server, only if it is not already
                if component.url is None:
                    component.register()
        # **** Node joigning information
        elif data['id'] == 'node_id_indicator':
            # A new sensor is joigning
            # Can't do anything of it because we don't have the gpio in the message so let's forget it...
            return
        # **** Node identification
        elif data['command'] == b'NI':
            # If we're not initialized yet, do nothing
            if self.initialized is False:
                return
            # Process answers to Node Identifier (NI) calls
            zb_id = data['parameter']
            zb_addr = data['source_addr_long']
            component = self.find_by_addr(zb_addr)
            # Update the name
            if component is None:
                # Not found ! Let's add it
                new_zb_sensor = self.create_component(ZIGBEE_TYPE, SENSOR_COMPONENT, name=zb_id, addr=zb_addr)
                self.add_component(new_zb_sensor)
                # Add link to server
                new_zb_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user,
                                                self.server_password)
            else:
                component.name = zb_id
                # Register it to the server, only if it is not already
                if component.url is None:
                    component.register()
        # **** Unknown message
        else:
            # We are receiving an answer to a question so let put it in the queue
            # even if we're not initialized yet
            self.zb_link.packets.put(data, block=False)
        return

    # This is a call back function for the ZigBee network incoming messages
    def callback_enOcean(self, data):
        try:
            from enocean.protocol.packet import Packet
            from enocean.protocol.constants import PACKET, RORG
        except:
            print("enOcean support is not available")
            raise

        # **** Automatic Sample
        if (data.type == PACKET.RADIO) and (data.rorg == RORG.BS4):
            # Check if we know the sender
            component = self.find_by_addr(data.sender)

            if component is None:
                # New component, is this a learn sample ?
                if data.learn is True:
                    new_enOcean_sensor = self.create_component(ENOCEAN_TYPE, SENSOR_COMPONENT,
                                                               name=DEFAULT_ENOCEAN_NAME, addr=data.sender,
                                                               enOcean_link=self.enOcean_link, rorg=data.rorg,
                                                               rorg_func=data.rorg_func, rorg_type=data.rorg_type)
                    self.add_component(new_enOcean_sensor)
                    # Add link to server
                    new_enOcean_sensor.add_config_server(self.client_hostname, self.server_host,
                                                         self.server_user, self.server_password)
                    # Register it to the server
                    new_enOcean_sensor.register()
            else:
                # If component is active then store the temperature
                if component.status is True:
                    try:
                        # Convert EEP
                        for k in data.parse_eep(component.rorg_func, component.rorg_type):
                            parsed_data = data.parsed[k]
                            temperature = parsed_data['value']
                        # Update the value
                        component.last_value = round(temperature, 3)
                        component.last_value_dt = datetime.datetime.now(component.timezone)
                        # Send it to the server
                        component.upload()
                    except:
                        print("Error processing a sample (data : ", data, ")")
        return
