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
import threading
import time
from common import consts
from core.msghandler import MessageNotifier, MessageHandler


class TransportMessageNotifier(MessageNotifier):
    pass


class TransportHandler(MessageHandler):

    def __init__(self, config=None, transport_index=0):
        super(TransportHandler, self).__init__(config=config)
        self._transport_thread = threading.Thread(target=self.listen)
        self._transport_index = transport_index
        self._transport_address = None
        self._transport_port = None
        self._transport_username = None
        self._transport_password = None
        self._transport_channel = None
        self._transport_client_id = None

    def do_listen(self):
        pass

    def do_configure(self):
        self._transport_address = self.get_config_value(consts.MQ_TRANSPORT_ADDR, "127.0.0.1")
        self._transport_port = self.get_config_value(consts.MQ_TRANSPORT_PORT, None)
        self._transport_username = self.get_config_value(consts.MQ_TRANSPORT_USER, None)
        self._transport_password = self.get_config_value(consts.MQ_TRANSPORT_PASS, None)
        self._transport_channel = self.get_config_value(consts.MQ_TRANSPORT_CHANNEL, None)
        self._transport_client_id = self.get_config_value(consts.MQ_TRANSPORT_CLIENTID, None)

    def do_start(self):
        if self.is_enabled():
            self._transport_thread.start()

    def listen(self):
        while self.is_running():
            try:
                self.do_listen()
            except Exception as ex:
                logging.error(ex)
                if self.is_running():
                    time.sleep(5)

    def get_transport_index(self):
        return self._transport_index

    def get_transport_address(self):
        return self._transport_address

    def get_transport_port(self):
        return self._transport_port

    def get_transport_user(self):
        return self._transport_username

    def get_transport_password(self):
        return self._transport_password

    def get_transport_channel(self):
        return self._transport_channel

    def get_transport_client_id(self):
        return self._transport_client_id

    def set_transport_index(self, index):
        self._transport_index = index

    def set_transport_address(self, address):
        self._transport_address = address

    def set_transport_port(self, port):
        self._transport_port = port

    def set_transport_user(self, username):
        self._transport_username = username

    def set_transport_password(self, passwd):
        self._transport_password = passwd

    def set_transport_channel(self, channel):
        self._transport_channel = channel

    def set_transport_client_id(self, client_id):
        self._transport_client_id = client_id

    def get_config_value(self, key, def_value):
        config_key = str(key).format(self._transport_index)
        return super(TransportHandler, self).get_config_value(config_key, def_value)

    def connect(self):
        raise NotImplementedError("not implemented here")

    def disconnect(self):
        raise NotImplementedError("not implemented here")

    def publish_message(self, message_obj):
        raise NotImplementedError("not implemented here")

    def notify_server(self, message_obj):
        raise NotImplementedError("notify_server not implemented here")
