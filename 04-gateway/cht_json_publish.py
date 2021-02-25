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
import gw_rx
import random
import json
import time
import sys

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
    client.publish(mqtt_topic, payload=data_json_string, qos=0, retain=False)

lora = LoRaRcvCont(verbose=False)
args = parser.parse_args(lora)
lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)

try:
    lora.init()
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    sleep(.5)
    BOARD.teardown()

try:
    while True:
        returnedList = lora.on_rx_done()
        
        client = mqtt.Client()
        
        # for tago include this line
        client.username_pw_set(mqtt_username, mqtt_password)
        
        client.on_connect = on_connect
        client.connect(broker, broker_port, mqtt_keep_alive)
        client.loop_start()
        
        data_json_string = json.dumps(returnedList)
        
        # 20 device every 2s
        time.sleep(2)

except KeyboardInterrupt:
    pass
