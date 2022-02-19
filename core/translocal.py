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
from threading import RLock


class LocalTransportHandler(TransportHandler):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    def __init__(self, config=None, transport_index=0):
        super(LocalTransportHandler, self).__init__(config=config, transport_index=transport_index)

    def send_shutdown_signal(self):
        pass

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
