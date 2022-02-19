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

import os
import re
import sys
import logging
import uvicorn
from dotenv import dotenv_values
from common import consts
from fastapi import FastAPI, APIRouter
from starlette.staticfiles import StaticFiles
from core.baseappsrv import BaseAppServer
from core.restprep import RESTModulePreparer
from core.redisprovider import RedisPreparer
from logging.handlers import TimedRotatingFileHandler


class RestApp(BaseAppServer):

    def __init__(self):
        super(RestApp, self).__init__()
        self.rest_app = None

    def do_configure(self):
        config = self.get_configuration()
        mode = "false" if consts.PRODUCTION_MODE not in config else config[consts.PRODUCTION_MODE]
        mode = "false" if mode is None else mode
        consts.IS_PRODUCTION_MODE = mode.lower() == "true"
        consts.DEFAULT_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
        RedisPreparer.prepare_redis(config, self)
        self.configure_rest_app()
        self.register_rest_modules()

    def configure_rest_app(self):
        self.rest_app = FastAPI(title="iBridge Server")
        self.rest_app.mount("/static", StaticFiles(directory=os.path.join(consts.DEFAULT_SCRIPT_PATH,
                                                                          "resources/static")),name="static")

        @self.rest_app.get("/", tags=["root"])
        async def index():
            return {'message': 'Welcome to iBridge Integration REST API'}

    @staticmethod
    def _get_klass(router_name):
        mod = None
        components = router_name.split(".")
        import_modules = ".".join(components[:-1])
        try:
            mod = __import__(import_modules)
            for cmp in components[1:]:
                mod = getattr(mod, cmp)
        except Exception as ex:
            logging.exception(ex)
        return mod

    def register_rest_modules(self) -> FastAPI:
        config = self.get_configuration()
        rest_services = config[consts.RESTAPI_AVAILABLE_SERVICES] if \
            consts.RESTAPI_AVAILABLE_SERVICES in config else None
        rest_services = rest_services if rest_services else ""
        rest_services = [service.strip() for service in rest_services.split(",") if service not in [None, '']]
        for mod_name in rest_services:
            mod = self._get_klass(mod_name)
            if isinstance(mod, APIRouter):
                self.rest_app.include_router(mod)
            elif mod and (issubclass(mod, RESTModulePreparer) or isinstance(mod, RESTModulePreparer)):
                mod.register_api_router(config, self.rest_app)
        return self.rest_app

    def get_rest_app(self):
        self.configure()
        return self.rest_app

    __call__ = get_rest_app


def configure_logging(config):
    default_level = consts.log_level[config[consts.LOG_LEVEL]] if consts.LOG_LEVEL in config \
        else consts.DEFAULT_LOG_LEVEL
    log_format = config[consts.LOG_FORMAT] if consts.LOG_FORMAT in config else consts.DEFAULT_LOG_FORMAT
    log_date_format = consts.DEFAULT_LOG_DATE_FORMAT
    log_file = config[consts.RESTAPI_LOG_FILE] if consts.RESTAPI_LOG_FILE in config else consts.DEFAULT_RESTAPI_LOG_FILE
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=5)
    logging.basicConfig(format=log_format, datefmt=log_date_format, handlers=[handler], level=default_level)


def create_app():
    config = dotenv_values(".env")
    configure_logging(config)

    rest_app_instance = RestApp.get_default_instance()
    rest_app_instance.set_configuration(config)
    return rest_app_instance()


app = create_app()

if __name__ == '__main__':
    is_debug = not consts.IS_PRODUCTION_MODE
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(uvicorn.run("irest:app", debug=is_debug, reload=True))
