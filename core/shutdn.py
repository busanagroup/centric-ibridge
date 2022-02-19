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
import traceback
from threading import Thread, RLock
from socket import AF_INET, socket, SOCK_STREAM
from core.startable import Startable
from common import consts
import logging
import selectors


class ShutdownHookMonitor(Startable):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    def __init__(self, config=None):
        super(ShutdownHookMonitor, self).__init__(config=config)
        self.socket = None
        self.selector = None
        self.shutdown_thread = None
        self.shutdown_addr = None
        self.shutdown_port = None

    def send_shutdown_signal(self):
        config = self.get_configuration()
        self.shutdown_addr = config[consts.SHUTDOWN_ADDR] if config and consts.SHUTDOWN_ADDR in config \
            else consts.DEFAULT_SHUTDOWN_ADDR
        self.shutdown_port = config[consts.SHUTDOWN_PORT] if config and consts.SHUTDOWN_PORT in config \
            else consts.DEFAULT_SHUTDOWN_PORT
        self.shutdown_port = int(self.shutdown_port) if isinstance(self.shutdown_port, str) else self.shutdown_port
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((self.shutdown_addr, self.shutdown_port))
        try:
            fd = client.makefile(mode="w")
            try:
                fd.write("shut\n")
                fd.flush()
            finally:
                fd.close()
        finally:
            client.close()

    def join(self, timeout=None):
        if not self.is_running():
            raise Exception("Shutdown Listener is not Running")
        self.shutdown_thread.join(timeout)

    def do_configure(self):
        config = self.get_configuration()
        self.selector = selectors.DefaultSelector()
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.shutdown_addr = config[consts.SHUTDOWN_ADDR] if config and consts.SHUTDOWN_ADDR in config \
            else consts.DEFAULT_SHUTDOWN_ADDR
        self.shutdown_port = config[consts.SHUTDOWN_PORT] if config and consts.SHUTDOWN_PORT in config \
            else consts.DEFAULT_SHUTDOWN_PORT
        self.shutdown_port = int(self.shutdown_port) if isinstance(self.shutdown_port, str) else self.shutdown_port
        self.shutdown_thread = Thread(target=self.listen, daemon=True, name="StopMonitor")

    def do_start(self):
        self.shutdown_thread.start()

    def do_stop(self):
        if not self.socket:
            return
        try:
            self.socket.close()
        except Exception as ex:
            logging.exception(ex)

    def listen(self):
        should_terminate = False
        self.socket.bind((self.shutdown_addr, self.shutdown_port))
        self.socket.setblocking(False)
        self.socket.listen(1)
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
                        finally:
                            event_socket.close()
            except Exception as ex:
                logging.error(ex)
            finally:
                self.stop() if should_terminate else None

    @classmethod
    def get_default_instance(cls):
        cls.SINGLETON_LOCK.acquire(blocking=True)
        try:
            if cls.VM_DEFAULT is None:
                cls.VM_DEFAULT = object.__new__(cls)
                cls.VM_DEFAULT.__init__()
            return cls.VM_DEFAULT
        finally:
            cls.SINGLETON_LOCK.release()
