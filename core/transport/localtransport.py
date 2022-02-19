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
import socket
import selectors
import traceback

from common import consts
from core.translocal import LocalTransportHandler


class LocalhostTransport(LocalTransportHandler):

    def __init__(self, config=None, transport_index=0):
        super(LocalhostTransport, self).__init__(config=config, transport_index=transport_index)
        self.socket = None
        self.selector = None

    def do_configure(self):
        super(LocalhostTransport, self).do_configure()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        
    def do_stop(self):
        super(LocalhostTransport, self).do_stop()
        if not self.socket:
            return
        try:
            self.socket.close()
        except Exception as ex:
            logging.exception(ex)

    def do_listen(self):
        should_terminate = False
        self.socket.bind((consts.LOCAL_TRANSPORT_ADDR, consts.LOCAL_TRANSPORT_PORT))
        self.socket.setblocking(False)
        self.socket.listen()
        self.selector.register(self.socket, selectors.EVENT_READ)
        while self.is_running():
            try:
                events = self.selector.select(timeout=2)
                for ev, _ in events:
                    event_socket = ev.fileobj
                    if event_socket == self.socket:
                        conn, __ = event_socket.accept()
                        conn.setblocking(False)
                        self.selector.register(conn, selectors.EVENT_READ)
                    else:
                        try:
                            fp = event_socket.makefile('r', buffering=1024)
                            message = fp.readline()
                            fp.close()
                            should_terminate = isinstance(message, str) and (message.strip().lower() == 'shut')
                            if not should_terminate:
                                self.handle_message(message)
                        finally:
                            event_socket.close()
            except Exception as ex:
                logging.error(ex)
            finally:
                self.stop() if should_terminate else None

    def connect(self):
        raise NotImplementedError("not implemented here")

    def disconnect(self):
        raise NotImplementedError("not implemented here")

    def publish_message(self, message_obj):
        raise NotImplementedError("not implemented here")

    def notify_server(self, message_obj):
        raise NotImplementedError("notify_server not implemented here")

    def notify_server(self, message_obj):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((consts.LOCAL_TRANSPORT_ADDR, consts.LOCAL_TRANSPORT_PORT))
        try:
            fd = client.makefile(mode="w")
            try:
                fd.write("{0}\n".format(message_obj.encode().decode("utf-8")))
                fd.flush()
            finally:
                fd.close()
        finally:
            client.close()

    def send_shutdown_signal(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((consts.LOCAL_TRANSPORT_ADDR, consts.LOCAL_TRANSPORT_PORT))
        try:
            fd = client.makefile(mode="w")
            try:
                fd.write("shut\n")
                fd.flush()
            finally:
                fd.close()
        finally:
            client.close()
