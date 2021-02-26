#!/usr/bin/env python3
# -*- coding: utf8 -*-
""" A simple continuous receiver class. """
# Copyright 2015 Mayer Analytics Ltd.
#
# This file is part of pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.

import paho.mqtt.client as mqtt
import random
import json
import time
import sys
from time import sleep
import packer
import socket
import numpy as np
sys.path.insert(0, '../')
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from SX127x.LoRaArgumentParser import LoRaArgumentParser

BOARD.setup()

parser = LoRaArgumentParser("Continous LoRa receiver.")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

# python2
try:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


# publish to TagoIO
device_token = "75942942-5468-4e7a-8890-2e9586ce6b55"
broker = "mqtt.tago.io"
broker_port = 1883
mqtt_keep_alive = 60
mqtt_username = "mqtt_client"
mqtt_password = device_token
mqtt_topic = "tago/data/post"

# publish emqx
# broker = "broker.emqx.io"
# broker_port = 1883
# mqtt_keep_alive = 60
# mqtt_topic = "topic/test"

def on_connect(client, userdata, flags, rc):
    print("Connected OK")
    client.publish(mqtt_topic, payload=rc, qos=0, retain=False)

class LoRaRcvCont(LoRa):
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0,0,0,0,0,0])    # RX
        self._id = "GW_01"


    def on_rx_done(self):
        print("\nRxDone")
        print('----------------------------------')

        payload = self.read_payload(nocheck=True)
        data = ''.join([chr(c) for c in payload])

        try:
            _length, _data = packer.Unpack_Str(data)
            print("Time: {}".format( str(time.ctime() )))
            print("Length: {}".format( _length ))
            print("Raw RX: {}".format( payload ))

            try:
                # python3 unicode
                print("Receive: {}".format( _data.encode('latin-1').decode('unicode_escape')))
            except:
                # python2
                print("Receive: {}".format( _data ))
        except:
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print("Non-hexadecimal digit found...")
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print("Receive: {}".format( data))



        self.set_dio_mapping([1,0,0,0,0,0])    # TX
        self.set_mode(MODE.STDBY)
  
        sleep(1)
        self.clear_irq_flags(TxDone=1)
        data = {"id":self._id, "data":packer.ACK}
        _length, _ack = packer.Pack_Str( json.dumps(data) )
        data_json = {'variable': 'payload', 'value': _ack}

        try:
            # for python2
            ack = [int(hex(ord(c)), 0) for c in _ack]
        except:
            # for python3 
            ack = [int(hex(c), 0) for c in _ack]

        print("ACK: {}, {}".format( self._id, ack))
        self.write_payload(ack)    
        self.set_mode(MODE.TX)
        return data_json


    def on_tx_done(self):
        print("\nTxDone")
        self.set_dio_mapping([0,0,0,0,0,0])    # RX
        self.set_mode(MODE.STDBY)
        sleep(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        self.clear_irq_flags(RxDone=1)


    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(1)
            rssi_value = self.get_rssi_value()
            status = self.get_modem_status()
            
            returnedList = self.on_rx_done()
            print("payload")
            client = mqtt.Client()
            
            # for tago include this line
            client.username_pw_set(mqtt_username, mqtt_password)
            
            client.on_connect = on_connect
            client.connect(broker, broker_port, mqtt_keep_alive, json.dumps(returnedList))
            client.loop_start()

            # 20 device every 2s
            time.sleep(2)

            sys.stdout.flush()
            sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))


lora = LoRaRcvCont(verbose=False)
args = parser.parse_args(lora)
lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)

print(lora)
assert(lora.get_agc_auto_on() == 1)

try: input("Press enter to start...")
except: pass

try:
    lora.start()
    #while True:
    
except KeyboardInterrupt:
    sys.stdout.flush()
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    sleep(.5)
    BOARD.teardown()

