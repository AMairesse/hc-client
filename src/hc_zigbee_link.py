import serial
import time

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
            print("Error opening serial port (", port, ")")
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

    # send a command
    def send(self, addr, command, parameter, frame_id):
        if parameter is None:
            self.zb.send('remote_at', command=command, dest_addr_long = addr, frame_id = frame_id)
        else:
            self.zb.send('remote_at', command=command, parameter=parameter, dest_addr_long = addr, frame_id = frame_id)
        nb_try = 4
        # Read responses
        while nb_try > 0:
            if self.packets.qsize() > 0:
                data = self.packets.get_nowait()
                # do not care of other packets
                if (data['command'] != command) or (data['frame_id'] != frame_id):
                    continue
                if data['status'] != b'\x00':
                    return False
                else:
                    return data
            else:
                time.sleep(1)
                nb_try = nb_try - 1
        return False

    # Broadcast command to the whole zigbee network
    def broadcast(self, command, frame_id):
        self.zb.send('at', command=command, frame_id = frame_id)
        return

    # Send a Node Identifier (NI) message to a zigbee
    # in order to register him
    def identify(self, addr):
        self.zb.send(addr, b'NI', None, b'8')
        return

