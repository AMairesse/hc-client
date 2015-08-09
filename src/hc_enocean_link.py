from enocean.communicators.serialcommunicator import SerialCommunicator

class enOcean_link(dict):
    # Public attribute
    packets = None
    
    def __init__(self, port, callback):
        # Initialize parent class
        super(enOcean_link, self).__init__()

        # Set port
        try:
            c = SerialCommunicator(port=port, callback=callback)
            c.start()
            #p = Packet(PACKET.COMMON_COMMAND, [0x08])
            #c.send(p)
        except:
            print ("Error opening serial port (", port, ")")
            raise

        return
    
    def stop(self):
        if c.is_alive():
            c.stop()
        return
