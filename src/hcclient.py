#!/usr/bin/env python

try:
    import configparser
except ImportError:
  import ConfigParser as configparser #for 2.x
import os, signal, socket, time
from hc_zigbee_link import Zigbee_link
from hc_enocean_link import enOcean_link
from hc_components import Components


# statics
INI_FILE= "/etc/hc-client.conf"
DEFAULT_HOST= 'http://localhost:8000/hc'
DEFAULT_USER= ''
DEFAULT_PASSWORD= ''

# on interrupt
def on_exit(sig, func=None):
    if 'components' in globals():
        global components
        components.stop()
        del components
    if 'zb_link' in globals():
        global zb_link
        zb_link.stop()
        del zb_link
    exit()

# Load config file
def load_config():
    ini_file = os.path.expanduser(INI_FILE)
    config = configparser.ConfigParser()
    if (os.path.isfile(ini_file)):
        config.read(ini_file)
        server_credential = {}
        try:
            server_credential['host'] = config.get('Server', 'host')
            server_credential['user'] = config.get('Server', 'user')
            server_credential['password'] = config.get('Server', 'password')
            # TODO : change 'Client' below to 'ZigBee'
            zigbee_serial_port = config.get('Client', 'serial_port')
            enOcean_serial_port = config.get('enOcean', 'serial_port')
        except:
            return False
        try:
            client_hostname = config.get('Client', 'hostname')
        except :
            client_hostname = socket.gethostname()
    else:
        # Print an error message
        print ("Config file not found (", INI_FILE, ")")
        return False
    return [server_credential, client_hostname, zigbee_serial_port, enOcean_serial_port]

# -----------------------------------
# main
# -----------------------------------
#def main():
#try:
# handle SIGTERM signal
signal.signal(signal.SIGTERM, on_exit)

# load config file
config = load_config()
if (config == False):
    # Print an error message and exit
    print ("Config file error (", INI_FILE, ")")
    exit()
else:
    [server_credential, client_hostname, zigbee_serial_port, enOcean_serial_port] = config

# Create a components container
components = Components()

# Create a ZigBee interface
zb_link = Zigbee_link(zigbee_serial_port, 9600, components.callback_ZB)
enOcean_link = enOcean_link(enOcean_serial_port, components.callback_enOcean)

# Load components
components.set_zb_link(zb_link)
components.set_enOcean_link(enOcean_link)
components.add_config_server(client_hostname, server_credential['host'], server_credential['user'], server_credential['password'])
components.initialize()
components.start()

# main loop
while (components.isAlive()):
    time.sleep(1)
#except:
#    # nothing to do but raise the exception
#    raise
#finally:
#    # Here we are sure to unset every GPIO set during program execution
#    on_exit(None)
#
#if __name__ == "__main__":
#    main()
