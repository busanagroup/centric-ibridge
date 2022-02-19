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
import time
import traceback

import amqp
import logging
from common import consts
from core.transhandler import TransportHandler


class AmqpTransport(TransportHandler):
    def __init__(self, config=None, transport_index=0):
        super(AmqpTransport, self).__init__(config=config, transport_index=transport_index)
        self._connection = None

        self.amqp_config = None
        self.host = None
        self.durable = True
        self.auto_delete = True
        self.type = "direct"
        self._transport_exchange = None

    def do_configure(self):
        super(AmqpTransport, self).do_configure()
        host = "{0}:{1}".format(self.get_transport_address(), self.get_transport_port())
        self._transport_exchange = self.get_config_value(consts.MQ_TRANSPORT_EXCHANGE, None)
        self._connection = amqp.Connection(host=host, userid=self.get_transport_user(),
                                           password=self.get_transport_password(),
                                           exchange=self.get_transport_channel(),
                                           heartbeat=10, read_timeout=2)

    @staticmethod
    def close_object(obj):
        if not obj:
            return
        try:
            obj.close()
        except Exception as ex:
            logging.exception(ex)

    def on_message_received(self, message):
        message.channel.basic_ack(message.delivery_tag)
        self.handle_message(message.body)

    def do_listen(self):
        self.connect()
        try:
            channel = self._connection.channel()
            channel.queue_declare(queue=self.get_transport_channel(), passive=True,
                                  durable=self.durable, auto_delete=self.auto_delete)
            channel.exchange_declare(exchange=self._transport_exchange, type=self.type,
                                     durable=self.durable, auto_delete=self.auto_delete)
            channel.queue_bind(queue=self.get_transport_channel(), exchange=self._transport_exchange)
            channel.basic_consume(callback=self.on_message_received)
            try:
                while self.is_running() and (not self._connection.blocking_read(timeout=2)):
                    time.sleep(0.4)
            finally:
                self.close_object(channel)
        except Exception as ex:
            logging.exception(ex)
        finally:
            self.disconnect()

    def connect(self):
        self._connection.connect()

    def disconnect(self):
        self.close_object(self._connection)

    def publish_message(self, message_obj):
        channel = self._connection.channel()
        channel.queue_declare(queue=self.get_transport_channel())
        channel.basic_publish(exchange='', routing_key=self.get_transport_channel(),
                              body=message_obj.encode().decode("utf-8"))

    def notify_server(self, message_obj):
        self.connect()
        try:
            self.publish_message(message_obj)
        finally:
            self.disconnect()
