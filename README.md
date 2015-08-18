=========
hc-client
=========

hc-client is a python client to be used with home_automation.
Together these two components manage a home heating system :
 * manage one or more temperature sensors
 * set rules for each sensor according to time period in the week
 * power one or more heaters with a regulation rule (hysteresis or proportional-integral)


=================
Supported devices
=================

hc-client can :
 * work wth a zigbee network
   * receive temperature values from an autonomous sensor
   * read temperature values at given frequency from an always-on sensor
   * start or stop a heater plugged on a zigbee
 * work with a 1-wire sensor available locally


===========================
home_automation interaction
===========================

hc-client will take instruction from heat_control (the django app from 
home_automation) to read from sensors and update heaters status.


============================
Install
============================
Launch :
sudo python setup.py install


============================
Requirements
============================
Software :
  * Python 2.7 or above (including 3.x)
  * requests (package python-requests or python3-requests)
  * pytz (package python-tz or python3-tz)
  * dateutil (package python-dateutil or python3-dateutil)
  * serial (package python-serial or python3-serial)
  * python-xbee 2.1
    Note : python-xbee v2.1 raise an error for packet size and this always occur when using an autonomous sensor.
           Modifying file /xbee/base.py line 277 and remplacing "raise ValueError" by "print" is recommended for stability
  * python-enocean (git master after Aug 10 2015 or version superior to 0.21 if available)
  * (optionnal) Rpi
  * (optionnal if older python) json
