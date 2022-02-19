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
from core.baseappsrv import BaseAppServer
from core.redisprovider import RedisPreparer
from core.shutdn import ShutdownHookMonitor
from core.transfactory import TransportPreparer
from core.msghandler import QueuePoolHandler, MessageNotifier
from core.msgexec import MessageExecutionManager
from core.msgpexec import ProcessMessageExecutionManager
from utils import transhelper


class BridgeServer(BaseAppServer):

    def __init__(self, config=None, standalone: bool = True):
        super(BridgeServer, self).__init__(config=config, standalone=standalone)

    def do_configure(self):
        cfg = self.get_configuration()
        RedisPreparer.prepare_redis(cfg, self)
        transport_listener = self.configure_transport()
        TransportPreparer.prepare_transports(cfg, transport_listener, self)

        local_transport = transhelper.get_local_transport()
        local_transport.set_configuration(cfg)
        local_transport.add_listener(transport_listener)
        self.add_object(local_transport)

        message_listener = MessageNotifier()
        execution_manager = MessageExecutionManager(cfg) if not self.is_production_mode() \
            else ProcessMessageExecutionManager(cfg)
        execution_manager.register_listener(message_listener)
        self.add_object(execution_manager)

        message_pool = QueuePoolHandler()
        message_pool.register_listener(transport_listener)
        message_pool.add_listener(message_listener)
        self.add_object(message_pool)

        if self.is_standalone():
            shutdown_hook = ShutdownHookMonitor.get_default_instance()
            shutdown_hook.set_configuration(cfg)
            shutdown_hook.add_listener(transport_listener)
            self.add_object(shutdown_hook)

        super(BridgeServer, self).do_configure()

    def handle_stop_event(self, obj):
        self.stop()
        logging.info("Shutting down bridge")

    def send_shutdown_signal(self):
        if self.is_standalone():
            return
        try:
            shutdown_monitor = self.get_object(ShutdownHookMonitor)
            shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
            shutdown_monitor.send_shutdown_signal() if shutdown_monitor else None
        except Exception as ex:
            print("Unable to connect to server")

    def notify_server(self, message_obj):
        try:
            config = self.get_configuration()
            local_transport = transhelper.get_local_transport()
            local_transport.set_configuration(config)
            local_transport.notify_server(message_obj)
        except Exception as ex:
            print("Unable to connect to server")

    def alt_shutdown_signal(self):
        try:
            config = self.get_configuration()
            local_transport = transhelper.get_local_transport()
            local_transport.set_configuration(config)
            local_transport.send_shutdown_signal()
        except Exception as ex:
            print("Unable to connect to server")

    def join(self):
        if self.is_standalone():
            return
        shutdown_monitor = self.get_object(ShutdownHookMonitor)
        shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
        shutdown_monitor.join() if shutdown_monitor else None

