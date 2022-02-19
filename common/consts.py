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

PRODUCTION_MODE = "production.mode"

SHUTDOWN_ADDR = "shutdown.addr"
SHUTDOWN_PORT = "shutdown.port"

KRAKEN_REST_BASE_URL = "kraken.rest.base.url"
KRAKEN_REST_USERNAME = "kraken.rest.username"
KRAKEN_REST_PASSWORD = "kraken.rest.password"

C8_REST_BASE_URL = "c8.rest.base.url"
C8_REST_USERNAME = "c8.rest.username"
C8_REST_PASSWORD = "c8.rest.password"

BRIDGE_ENABLED = "bridge.enabled"

RESTAPI_ENABLED = "restapi.enabled"
RESTAPI_ROOT_PATH = "restapi.root.path"
RESTAPI_SECRET_KEY = "restapi.secret.key"
RESTAPI_ADMIN_USERNAME = "restapi.admin.username"
RESTAPI_AVAILABLE_SERVICES = "restapi.available.services"

LOG_LEVEL = "log.level"
LOG_FORMAT = "log.format"
LOG_FILE = "log.file"
RESTAPI_LOG_FILE = "restapi.log.file"

REDIS_ENABLED = "redis.enabled"
REDIS_URL = "redis.url"

MQ_TRANSPORT_COUNT = "mq.transport.count"
MQ_TRANSPORT_TYPE = "mq.transport.{0}.type"
MQ_TRANSPORT_ADDR = "mq.transport.{0}.address"
MQ_TRANSPORT_PORT = "mq.transport.{0}.port"
MQ_TRANSPORT_USER = "mq.transport.{0}.user"
MQ_TRANSPORT_PASS = "mq.transport.{0}.passwd"
MQ_TRANSPORT_CHANNEL = "mq.transport.{0}.channel"
MQ_TRANSPORT_CLIENTID = "mq.transport.{0}.clientid"
MQ_TRANSPORT_HEARTBEAT = "mq.transport.{0}.heartbeat"
MQ_TRANSPORT_EXCHANGE = "mq.transport.{0}.exchange"

LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "WARNING"
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_CRITICAL = "CRITICAL"

log_level = {LOG_LEVEL_INFO: logging.INFO,
             LOG_LEVEL_WARNING: logging.WARNING,
             LOG_LEVEL_DEBUG: logging.DEBUG,
             LOG_LEVEL_ERROR: logging.ERROR,
             LOG_LEVEL_CRITICAL: logging.CRITICAL}

DEFAULT_SCRIPT_PATH = "./"
DEFAULT_COMMAND_FILE = "commands.properties"
DEFAULT_EVENT_FILE = "events.properties"

DEFAULT_LOG_FORMAT = "%(asctime)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_FILE = "{0}/log/ibridge.log".format(DEFAULT_SCRIPT_PATH)
DEFAULT_RESTAPI_LOG_FILE = "{0}/log/irest.log".format(DEFAULT_SCRIPT_PATH)
DEFAULT_LOG_LEVEL = log_level[LOG_LEVEL_INFO]

DEFAULT_SHUTDOWN_ADDR = "127.0.0.1"
DEFAULT_SHUTDOWN_PORT = 9999

MQ_TRANSPORT_STOMP = "stomp"
MQ_TRANSPORT_MQTT = "mqtt"
MQ_TRANSPORT_AMQP = "amqp"
MQ_TRANSPORT_REDIS = "redis"
MQ_TRANSPORT_UNIX = "unix"
MQ_TRANSPORT_LOCAL = "local"

UNIX_SOCKET_FILE = "/tmp/ibridge.sock"
LOCAL_TRANSPORT_ADDR = "127.0.0.1"
LOCAL_TRANSPORT_PORT = 8888

MODULE_CONFIG_FILE = "modules.properties"

TRANSPORT_INFO = {MQ_TRANSPORT_UNIX: "core.transport.xsocktransport.UnixSocketTransport",
                  MQ_TRANSPORT_LOCAL: "core.transport.localtransport.LocalhostTransport",
                  MQ_TRANSPORT_STOMP: "core.transport.stomptransport.StompTransport",
                  MQ_TRANSPORT_MQTT: "core.transport.mqtttransport.MqttTransport",
                  MQ_TRANSPORT_AMQP: "core.transport.amqptransport.AmqpTransport",
                  MQ_TRANSPORT_REDIS: "core.transport.redistransport.RedisTransport"}

SERVICES_AVAILABLE = [["core.bridgesrv.BridgeServer", False],
                      ["core.reststarter.RESTServerStarter", False]]

BRIDGE_SERVICE = SERVICES_AVAILABLE[0][0]

IS_PRODUCTION_MODE = False
