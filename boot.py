import pycom
import time
import machine
from network import WLAN
from simple import MQTTClient
from machine import I2C
from machine import Timer
from machine import Pin
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
pycom.heartbeat(False)
wlan=WLAN(mode=WLAN.STA)
