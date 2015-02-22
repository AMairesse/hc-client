import serial
try:
    import queue
except ImportError:
  import Queue as queue #for 2.x
from xbee import ZigBee as ZB


class Zigbee_link(dict):
    # Public attribute
    packets = None
    zb = None

    def __init__(self, port, baud_rate, callback):
        # Initialize parent class
        super(Zigbee_link, self).__init__()
        # Set port and baud_rate
        self.port = port
        self.baud_rate = baud_rate
        # Open serial port
        try:
            self.ser = serial.Serial(self.port, self.baud_rate)
        except:
            print ("Error opening serial port (", port, ")")
            raise
        # Create a queue to receive message from the network
        self.packets = queue.Queue()
        # Create XBee library API object, which spawns a new thread with the callback function
        self.zb = ZB(self.ser, callback=callback)
        return
    
    def stop(self):
        self.zb.halt()
        self.ser.close()
        return
