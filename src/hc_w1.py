from hc_sensor import Sensor
import glob, os

# statics
W1_TYPE = "Default"
W1_BUS_DIRECTORY = "/sys/bus/w1/devices/"
W1_BUS_FILE = "/w1_slave"


class W1_sensor(Sensor):
    # Public attribute
    devicefile = None
            
    # Init method uses dict so we can pass any field for creation
    def __init__(self, **kwargs):
        super(W1_sensor, self).__init__(**kwargs)
        if (self.name != None):
            self.set_devicefile()
        return
    
    # Set device file for a sensor
    def set_devicefile(self):
        if (self.type == W1_TYPE):
            self.devicefile = W1_BUS_DIRECTORY + self.name  + W1_BUS_FILE
        else:
            print ("WARNING - Sensor : ", self.name, " is of an unknown type : ", self.type)
            self.devicefile = False
        return
    
    # Read a sensor value and update data within the object
    def update(self):
        # If no devicefile then do nothing
        if self.devicefile == None:
            return False
        try:
            # Open the file representing the sensor and read it
            fileobj = open(self.devicefile,'r')
            lines = fileobj.readlines()
            fileobj.close()
            # Find the temperature 10th bloc on 2nd line
            temperaturedata = lines[1].split(" ")[9]
            temperature = float(temperaturedata[2:])
        except:
            return False
        # If everything is ok then update the value
        self.last_value = temperature / 1000
        # Component class update's method
        return super(W1_sensor, self).update()


