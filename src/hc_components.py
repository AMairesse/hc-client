from hc_heater import Heater, HEATERS_PATH
from hc_sensor import Sensor, SENSORS_PATH
from hc_w1 import W1_sensor, W1_TYPE, W1_BUS_DIRECTORY, W1_BUS_FILE
import glob, os
import requests, json
import pytz, time, datetime
import threading

# statics
ZIGBEE_TYPE = 'ZigBee'
ENOCEAN_TYPE = 'enOcean'
W1_TYPE = "Default"
DEFAULT_TIMEZONE = 'UTC'
HEATER_COMPONENT_TYPE = 'Heater'
SENSOR_COMPONENT_TYPE = 'Sensor'
W1_COMPONENT_TYPE = 'W1 Sensor'


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
        return

    def __del__(self):
        # delete objects of the list
        for component in self.components_list :
            del component
        return

    def create_component(self, component_type, **kwargs):
        if (component_type == HEATER_COMPONENT_TYPE):
            component = Heater(**kwargs)
            component.component_type = HEATER_COMPONENT_TYPE
        elif (component_type == SENSOR_COMPONENT_TYPE):
            component = Sensor(**kwargs)
            component.component_type = SENSOR_COMPONENT_TYPE
        elif (component_type == W1_COMPONENT_TYPE):
            component = W1_sensor(**kwargs)
            component.component_type = W1_COMPONENT_TYPE
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
            if (component.status == True) & (component.freq != 0) :
                running_list.append(component)
        # If there is nothing in the list then do nothing and leave
        if (running_list == []):
            return
        # Otherwise keep updating...
        while (self.stay_running):
            result = self.update_next(running_list)
            if (result == False):
                break
        return

    def stop(self):
        self.stay_running = False
        while (self.isAlive()):
            time.sleep(0.1)
        return

    def detect(self):
        # Detect Zigbee components in the network
        # Send a Node Discover (ND) message to broadcast
        self.zb_link.zb.send('at', command=b'ND', frame_id = b'1')
        # Detect W1 components on the host
        devicelist = glob.glob(W1_BUS_DIRECTORY + '28*')
        for device in devicelist:
            devicefile = device + W1_BUS_FILE
            if os.path.exists(devicefile):
                [_, component_name] = device.rsplit('/', 1)
                component = self.find_by_name_and_type(component_name, W1_COMPONENT_TYPE, W1_TYPE)
                if (component == None):
                    new_w1_sensor = self.create_component(W1_COMPONENT_TYPE, name = component_name, type = W1_TYPE)
                    self.add_component(new_w1_sensor)
                    new_w1_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user, self.server_password)
                    new_w1_sensor.register()
        return


    def initialize(self):
        # Configure all components, add config server
        self.update_config_by_type(ZIGBEE_TYPE, HEATER_COMPONENT_TYPE, HEATERS_PATH)
        self.update_config_by_type(ZIGBEE_TYPE, SENSOR_COMPONENT_TYPE, SENSORS_PATH)
        self.update_config_by_type(W1_TYPE, W1_COMPONENT_TYPE, SENSORS_PATH)
        self.initialized = True
        # Detect components availables
        self.detect()
        # Initialize components
        for component in self.components_list :
            # Only initialize components with a positive status
            if (component.status == True):
                component.initialize()
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
        for component in self.components_list :
            component.add_config_server(client_hostname, server_host, server_user, server_password)
        return

    # Function to find by name and type
    def find_by_name_and_type(self, component_name, component_type, type):
        component = next((x for x in self.components_list if ((x.name == component_name) and (x.component_type == component_type) and (x.type == type))), None)
        return component
    
    # Function to find by addr
    def find_by_addr(self, addr):
        component = next((x for x in self.components_list if (x.addr == addr)), None)
        return component
    
    # Function to find by addr and gpio
    def find_by_addr_and_gpio(self, addr, gpio):
        component = next((x for x in self.components_list if ((x.addr == addr) and (x.gpio == gpio))), None)
        return component
    
    # Function to sort by refresh_dt
    def sort_by_refresh_dt(self, item):
        return item.refresh_dt()
    
    # Read component from config server
    def update_config_by_type(self, component_class, component_type, PATH):
        # Request known components for this host from the server
        requested_url = self.server_host + PATH + '/'
        try:
            if (self.server_user == None):
                r = requests.get(requested_url)
            else:
                r = requests.get(requested_url, auth=(self.server_user, self.server_password))
            text_response = json.loads(r.text)
            nb_result = text_response[u'count']
            results = text_response[u'results']
        except:
            # If we don't manage to get anything then just get out
            return
        # Process each result
        for i in range(nb_result):
            # Check if the zigbee is already known
            component_name = str(results[i][u'name']).encode('utf_8')
            type = str(results[i][u'type'])
            if (type != component_class):
                # Listed component is not of the type/class we are looking for
                # go on with the next one
                continue
            component = self.find_by_name_and_type(component_name, component_type, type)
            if (component == None):
                # New component, let's create it in the list
                component = self.create_component(component_type, name = component_name, type = results[i][u'type'], zb_link = self.zb_link)
                self.add_component(component)
                # Add link to server
                component.add_config_server(self.client_hostname, self.server_host, self.server_user, self.server_password)
            # Update the component parameters
            component.status = bool(results[i][u'status'])
            component.url = str(results[i][u'id'])
            component.freq = int(results[i][u'freq'])
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
        if (time_before_wait < next_refresh_dt):
            delta = next_refresh_dt - time_before_wait
            tenth_of_seconds_to_wait = int(delta.total_seconds() * 10)
            for i in range(tenth_of_seconds_to_wait):
                time.sleep(0.1)
                if (self.stay_running == False):
                    return
        # Update the component
        updated = component.update()
        # Upload data if a server is known
        if ((updated == True) and (self.server_host != None)):
            component.upload()
        elif (updated == False):
            # if update failed then update last_value_dt
            # to refresh_dt for next retry
            component.last_value_dt = component.refresh_dt()
        return

    # This is a call back function for the ZigBee network incoming messages
    def callback_ZB(self, data):
        # **** Automatic sample
        if (data['id'] == 'rx_io_data_long_addr'):
            # If we're not initialized yet, do nothing
            if (self.initialized == False):
                return
            # Process each sample
            samples = data['samples']
            for sample in samples:
                for item in sample:
                    gpio = int(item[4:])
                    value = int(sample[item])
                    # Search the component
                    component = self.find_by_addr_and_gpio(data['source_addr_long'], gpio)
                    if (component == None):
                        # New component, let's create it in the list
                        new_zb_sensor = self.create_component(SENSOR_COMPONENT_TYPE, name = None, type = ZIGBEE_TYPE, addr = data['source_addr_long'], zb_link = self.zb_link, gpio = gpio)
                        self.add_component(new_zb_sensor)
                        # Add link to server
                        new_zb_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user, self.server_password)
                        # Ask him for his name : send a Node Identifier (NI) message
                        new_zb_sensor.send(b'NI', None, b'8')
                    else:
                        if (component.url == None):
                            # The component is not registered yet, ask him for his name : send a Node Identifier (NI) message
                            component.send(b'NI', None, b'8')
                        elif (component.status == False):
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
                                print ("Error processing a sample (data : ", data, ")")
                                continue
        # **** Node discovery
        elif (data['command'] == b'ND'):
            # If we're not initialized yet, do nothing
            if (self.initialized == False):
                return
            # Process answers to Node Discovery (ND) calls
            zb_id = data['parameter']['node_identifier']
            zb_addr = data['parameter']['source_addr_long']
            component = self.find_by_addr(zb_addr)
            # Update the name
            if (component == None):
                # Not found ! Let's add it (sensor and heater)
                new_zb_sensor = self.create_component(SENSOR_COMPONENT_TYPE, name = zb_id, type = ZIGBEE_TYPE, addr = zb_addr, zb_link = self.zb_link)
                self.add_component(new_zb_sensor)
                new_zb_heater = self.create_component(HEATER_COMPONENT_TYPE, name = zb_id, type = ZIGBEE_TYPE, addr = zb_addr, zb_link = self.zb_link)
                self.add_component(new_zb_heater)
                # Add link to server
                new_zb_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user, self.server_password)
                new_zb_heater.add_config_server(self.client_hostname, self.server_host, self.server_user, self.server_password)
            else:
                component.name = zb_id
                # Register it to the server, only if it is not already
                if (component.url == None):
                    component.register()
        # **** Node joigning information
        elif (data['id'] == 'node_id_indicator'):
            # A new sensor is joigning
            # Can't do anything of it because we don't have the gpio in the message so let's forget it...
            return
        # **** Node identification
        elif (data['command'] == b'NI'):
            # If we're not initialized yet, do nothing
            if (self.initialized == False):
                return
            # Process answers to Node Identifier (NI) calls
            zb_id = data['parameter']
            zb_addr = data['source_addr_long']
            component = self.find_by_addr(zb_addr)
            # Update the name
            if (component == None):
                # Not found ! Let's add it
                new_zb_sensor = self.create_component(SENSOR_COMPONENT_TYPE, name = zb_id, type = ZIGBEE_TYPE, addr = zb_addr, zb_link = self.zb_link)
                self.add_component(new_zb_sensor)
                # Add link to server
                new_zb_sensor.add_config_server(self.client_hostname, self.server_host, self.server_user, self.server_password)
            else:
                component.name = zb_id
                # Register it to the server, only if it is not already
                if (component.url == None):
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
        except :
            print ("enOcean support is not available")
            raise
        
        print("enOcean msg received")
        print(data)
        
        # **** Automatic Sample
        if ((data.type == PACKET.RADIO) and (data.rorg == RORG.BS4)):
            # Check if we know the sender
            component = self.find_by_addr(data.sender)
            if (component == None):
                # New component, it this a learn sample ?
                if (data.learn == True):
                    new_enOcean_sensor = self.create_component(SENSOR_COMPONENT_TYPE, name = None,
                                                               type = ENOCEAN_TYPE, addr = data.sender,
                                                               enOcean_link = self.enOcean_link, rorg=data.rorg,
                                                               rorg_func=data.rorg_func, rorg_type = data.rorg_type)
                    self.add_component(new_enOcean_sensor)
                    # Add link to server
                    #new_enOcean_sensor.add_config_server(self.client_hostname, self.server_host,
                    #                                     self.server_user, self.server_password)
            else:
                try:
                    # Convert EEP
                    for k in data.parse_eep(component.rorg_func, component.rorg_type):
                        parsed_data = data.parsed[k]
                        temperature = parsed_data[u'value']
                        print("enOcean temperature read : ", temperature)
                    # Update the value
                    component.last_value = temperature
                    component.last_value_dt = datetime.datetime.now(component.timezone)
                    # Send it to the server
                    #component.upload()
                except:
                    print ("Error processing a sample (data : ", data, ")")
        return

