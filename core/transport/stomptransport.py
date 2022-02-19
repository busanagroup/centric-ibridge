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

from core.transhandler import TransportHandler
from stompest.config import StompConfig
from stompest.protocol.spec import StompSpec
from stompest.sync import Stomp
from common import consts
import logging
import time


class StompTransport(TransportHandler):

    def __init__(self, config=None, transport_index=0):
        super(StompTransport, self).__init__(config=config, transport_index=transport_index)
        self._stomp_config = None
        self._client_heartbeat = None
        self._stomp_client = None

    def do_configure(self):
        super(StompTransport, self).do_configure()
        self._client_heartbeat = self.get_config_value(consts.MQ_TRANSPORT_HEARTBEAT, 20000)
        self._stomp_config = StompConfig("tcp://{0}:{1}".format(self.get_transport_address(),
                                                                self.get_transport_port()),
                                         login=self.get_transport_user(),
                                         passcode=self.get_transport_password(),
                                         version=StompSpec.VERSION_1_2)
        self._stomp_client = Stomp(self._stomp_config)

    def do_listen(self):
        logging.info("Subscribing {} on channel {}".format(self.get_transport_address(), self.get_transport_channel()))
        self.connect()
        try:
            client_heartbeat = self._stomp_client.clientHeartBeat / 1000.0
            token = self._stomp_client.subscribe(self.get_transport_channel(),
                                                 {StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
                                                  StompSpec.ID_HEADER: self.get_transport_client_id()})
            try:
                while self.is_running():
                    if self._stomp_client.canRead(2):
                        frame = self._stomp_client.receiveFrame()
                        cmd_str = frame.body
                        self._stomp_client.ack(frame)
                        self.handle_message(cmd_str)
                    else:
                        time.sleep(0.4)
                    if (time.time() - self._stomp_client.lastSent) > client_heartbeat:
                        self._stomp_client.beat()
            finally:
                self._stomp_client.unsubscribe(token)
        finally:
            self.disconnect()

    def get_client_heartbeat(self):
        return self._client_heartbeat

    def connect(self):
        self._stomp_client.connect(versions=[StompSpec.VERSION_1_2], heartBeats=(self.get_client_heartbeat(),
                                                                                 self.get_client_heartbeat()))

    def disconnect(self):
        self._stomp_client.disconnect()

    def publish_message(self, message_obj):
        self._stomp_client.send(self.get_transport_channel(), message_obj.encode().decode("utf-8"))

    def notify_server(self, message_obj):
        self.connect()
        try:
            self.publish_message(message_obj)
        finally:
            self.disconnect()
