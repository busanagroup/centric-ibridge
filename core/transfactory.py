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

from threading import RLock
from common import consts
from core.objfactory import AbstractFactory


class TransportFactory(AbstractFactory):
    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    def __init__(self, config=None):
        super(TransportFactory, self).__init__(config=config)
        self.dictionary = {}

    def do_configure(self):
        keys = [key for key in consts.TRANSPORT_INFO if key not in self.dictionary]
        self.dictionary.update([(key, self.import_klass(consts.TRANSPORT_INFO[key])) for key in keys])

    def has_protocol(self, name):
        return name in self.dictionary

    def create_transport(self, name, **kwargs):
        if not self.has_protocol(name):
            return None
        klass = self.dictionary[name]
        index = kwargs.pop("index", 0)
        config = self.get_configuration()
        instance = self.create_instance(klass)
        instance.set_configuration(config)
        instance.set_transport_index(index)
        return instance

    @classmethod
    def get_default_instance(cls, config):
        cls.SINGLETON_LOCK.acquire(blocking=True)
        try:
            if cls.VM_DEFAULT is None:
                cls.VM_DEFAULT = object.__new__(cls)
                cls.VM_DEFAULT.__init__()
                cls.VM_DEFAULT.set_configuration(config)
                cls.VM_DEFAULT.configure()
            return cls.VM_DEFAULT
        finally:
            cls.SINGLETON_LOCK.release()


class TransportPreparer(object):

    @classmethod
    def get_config_value(cls, config, key, index, default):
        formatted_key = key.format(index)
        return config[formatted_key] if formatted_key in config else default

    @classmethod
    def create_transport(cls, config, index):
        protocol = cls.get_config_value(config, consts.MQ_TRANSPORT_TYPE, index, None)
        factory = TransportFactory.get_default_instance(config)
        return factory.create_transport(protocol, index=index) if protocol and factory.has_protocol(protocol) else None

    @classmethod
    def prepare_transports(cls, config, listener, container):
        trans_count = config[consts.MQ_TRANSPORT_COUNT] if consts.MQ_TRANSPORT_COUNT in config else 0
        trans_count = int(trans_count)
        trans_count = 0 if trans_count <= 0 else trans_count
        for index in range(trans_count):
            instance = cls.create_transport(config, index)
            if instance:
                instance.add_listener(listener)
                container.add_object(instance)
