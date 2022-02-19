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
import traceback
import urllib.parse
from core.prochandler import CommandProcessor
from core.msgobject import mq_command
from utils.httpclient import HttpClient
from utils.basehttpclient import OAUTH2_AUTH
from utils.c8client import C8WebClient


class ExampleCommand(CommandProcessor):

    def __init__(self):
        super(ExampleCommand, self).__init__()
        self._module = "MODULE@EXAMPLE"
        self._props = None
        self._api_service = None

    def do_configure(self):
        prop = self.get_module_configuration()
        self._props = dict() if self._module not in prop else prop[self._module]

        config = self.get_configuration()
        base_url = self._props["LOCAL_API_URL"] if "LOCAL_API_URL" in self._props else "http://127.0.0.1:8000"
        username = self._props["LOCAL_API_USER"] if "LOCAL_API_USER" in self._props else "localuser@example.com"
        password = self._props["LOCAL_API_PASSWORD"] if "LOCAL_API_PASSWORD" in self._props else "localpassword"
        if not base_url or not username or not password:
            return
        self._api_service = C8WebClient(host_url=base_url, config=config,
                                        parent=self.get_parent(), auth_type=OAUTH2_AUTH)
        try:
            if not self._api_service.login_expired():
                return
            http_login = HttpClient(host_url=base_url)
            login_info = {'grant_type': 'password',
                          'username': username,
                          'password': password,
                          'scope': '',
                          'client_id': '',
                          'client_secret': ''}
            headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
            result = http_login.post("auth/jwt/login", data=urllib.parse.urlencode(login_info, doseq=True),
                                     headers=headers)
            if result.status_code == 200:
                self._api_service.update_login_info(result.json())
            else:
                logging.error("Failed to login to Local API Service with error code {0}".format(result.status_code))

        except Exception as ex:
            logging.exception(ex)

    @mq_command
    def example_command(self, cono=None, dvno=None):
        logging.info("Hello World COMMAND called with params cono={0}, dvno={1}".format(cono, dvno))

    @mq_command
    def call_restapi(self):
        if not self._api_service:
            return
        resource = self._api_service.create_resource("hello")
        try:
            result = resource.get()
            if result.status_code == 200:
                logging.info(result.json())
            else:
                logging.error("Failed to retrieve hello from Local API Service with error code {0}".format(
                    result.status_code))

        except Exception as ex:
            logging.exception(ex)
