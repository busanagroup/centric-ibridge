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
import logging
from common import consts
from core.prochandler import CommandProcessor
from core.msgobject import mq_command
from utils.c8client import C8WebClient
from utils.httpclient import HttpClient


class C8Example(CommandProcessor):

    def __init__(self):
        super(C8Example, self).__init__()
        self._module = 'CENTRIC@EXAMPLE'
        self._props = None
        self._c8rest_service = None

    def do_configure(self):
        prop = self.get_module_configuration()
        self._props = dict if self._module not in prop else prop[self._module]
        config = self.get_configuration()
        base_url = config[consts.C8_REST_BASE_URL] if consts.C8_REST_BASE_URL in config else None
        username = config[consts.C8_REST_USERNAME] if consts.C8_REST_USERNAME in config else None
        password = config[consts.C8_REST_PASSWORD] if consts.C8_REST_PASSWORD in config else None
        if not base_url or not username or not password:
            return
        self._c8rest_service = C8WebClient(config=config, parent=self.get_parent())
        try:
            if not self._c8rest_service.login_expired():
                return
            http_login = HttpClient(host_url=base_url)
            login_info = {"username": username,
                          "password": password}
            result = http_login.post("session", json_data=login_info)
            if result.status_code == 200:
                self._c8rest_service.update_login_info(result)
            else:
                logging.error("Failed to login to Centric API Service with error code {0}".format(result.status_code))

        except Exception as ex:
            logging.exception(ex)

    @mq_command
    def get_c8color_specs(self):
        if not self._c8rest_service:
            return
        resource = self._c8rest_service.create_resource("color_specifications")
        try:
            result = resource.get()
            if result.status_code == 200:
                logging.info(result.json())
            else:
                logging.error("Failed to retrieve color_spec from Centric API Service with error code {0}".format(result.status_code))


        except Exception as ex:
            logging.exception(ex)


