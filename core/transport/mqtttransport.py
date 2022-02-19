#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Busana Apparel Group. All rights reserved.
#
# This product and it's source code is protected by patents, copyright laws and
# international copyright treaties, as well as other intellectual property
# laws and treaties. The product is licensed, not sold.
#
# The source code and sample programs in this package or parts hereof
# as well as the documentation shall not be copied, modified or redistributed
# without permission, explicit or implied, of the author.
#
# This module is part of Centric PLM Integration Bridge and is released under
# the Apache-2.0 License: https://www.apache.org/licenses/LICENSE-2.0

import logging
import traceback
from uuid import uuid4
from paho.mqtt import client
from core.transhandler import TransportHandler


class MqttTransport(TransportHandler):

    def __init__(self, config=None, transport_index=0):
        super(MqttTransport, self).__init__(config=config, transport_index=transport_index)
        self.client = None
        self._subscribed = False

    def do_configure(self):
        super(MqttTransport, self).do_configure()
        self.set_transport_client_id(str(uuid4()))
        self.client = client.Client(self.get_transport_client_id())
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.get_transport_user(), self.get_transport_password())

    def on_message(self, client, usrdata, msg):
        self.handle_message(bytes(msg.payload.decode(), 'utf-8')) if msg else None

    def on_subscribe(self, client, obj, mid, granted_qos):
        self._subscribed = True

    def on_disconnect(self, client, userdata, rc):
        logging.info("Disconnected to mqtt broker")
        self._subscribed = False

    def on_connect(self, client, obj, flags, rc):
        logging.info("Connected to mqtt broker")
            
    def do_stop(self):
        super(MqttTransport, self).do_stop()
        self.client.loop_stop() if self.client else None

    def _force_unsubscribe(self):
        try:
            self.client.unsubscribe(self.get_transport_channel())
        except Exception as ex:
            logging.exception(ex)

    def _force_disconnect(self):
        try:
            self.client.disconnect()
        except Exception as ex:
            logging.exception(ex)

    def do_listen(self):
        logging.info("Subscribing {} on {}".format(self.get_transport_address(), self.get_transport_channel()))
        self.connect()
        try:
            self.client.subscribe(self.get_transport_channel())
            try:
                while self.is_running():
                    self.client.loop_start()
            finally:
                self._force_unsubscribe()
        finally:
            self.disconnect()

    def connect(self):
        if not self.client:
            self.do_configure()
        self.client.connect(self.get_transport_address(), int(self.get_transport_port()))

    def disconnect(self):
        self._force_disconnect()

    def publish_message(self, message_obj):
        self.client.publish(self.get_transport_channel(), message_obj.encode().decode("utf-8"))

    def notify_server(self, message_obj):
        self.connect()
        try:
            self.publish_message(message_obj)
        finally:
            self.disconnect()

