from enocean.communicators.serialcommunicator import SerialCommunicator


class enOcean_link(dict):
    # Public attribute
    packets = None
    
    def __init__(self, port, callback):
        # Initialize parent class
        super(enOcean_link, self).__init__()

        # Set debug mode if needed
        # from enocean.consolelogger import init_logging
        # init_logging()

        # Set port
        try:
            self.c = SerialCommunicator(port=port, callback=callback)
            self.c.start()
        except:
            print("Error opening serial port (", port, ")")
            raise

        return
    
    def stop(self):
        if self.c.is_alive():
            self.c.stop()
        return
