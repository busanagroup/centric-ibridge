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
from redis import Redis
from redis.connection import Connection, ConnectionPool
from common import consts
from core.startable import Startable, LifeCycleManager


class RedisProvider(Startable):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    def __init__(self, config=None):
        super(RedisProvider, self).__init__(config=config)
        self._pool = None
        self.service_enabled = False

    def do_configure(self):
        redis_url = self.get_config_value(consts.REDIS_URL, '')
        assert self.service_enabled, "Redis has not been enabled"
        service_enabled = redis_url not in ['', None]
        self.service_enabled = service_enabled
        assert service_enabled, "Redis URL is not provided, could not configure"
        self._pool = ConnectionPool.from_url(redis_url)

    def do_stop(self):
        self._pool.disconnect(inuse_connections=True)

    def get_pool(self):
        return self._pool

    def get_connection(self, command_name, *keys, **options):
        return self._pool.get_connection(command_name, *keys, **options)

    def release_connection(self, connection: Connection):
        self._pool.release(connection)

    def get_redis(self):
        return Redis(connection_pool=self._pool)

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


class RedisPreparer(object):

    @classmethod
    def prepare_redis(cls, cfg: dict, server_holder: LifeCycleManager):
        redis_enabled = server_holder.get_config_value(consts.REDIS_ENABLED, "false")
        redis_enabled = True if redis_enabled.lower() == "true" else False
        if redis_enabled:
            redis_instance = RedisProvider.get_default_instance()
            if not redis_instance.is_configured():
                redis_instance.set_configuration(cfg)
                redis_instance.service_enabled = True
                server_holder.add_object(redis_instance)
