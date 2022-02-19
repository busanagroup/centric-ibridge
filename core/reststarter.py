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
import signal
import subprocess
import logging
import sys
import time
import psutil
from common import consts
from utils import restutils, oshelper
from core.baseappsrv import BaseAppServer
import traceback


class RESTServerStarter(BaseAppServer):

    def __init__(self, config=None, standalone: bool = True):
        super(RESTServerStarter, self).__init__(config=config, standalone=standalone)

    def do_configure(self):
        super(RESTServerStarter, self).do_configure()
        
    def do_start(self):
        # only enable this on production mode in linux
        if self.is_production_mode() and oshelper.is_linux():
            pid_file = consts.DEFAULT_SCRIPT_PATH + '/data/temp/irest.pid'
            os.makedirs(os.path.dirname(pid_file), exist_ok=True)
            run_args = [
                consts.DEFAULT_SCRIPT_PATH + '/' +
                'websvcsvr',
                '-w', '4',
                '-k', 'uvicorn.workers.UvicornWorker',
                '-b', '0.0.0.0:8080',
                '-n', 'centric-rest-ibridge',
                '-p', str(pid_file),
                '--error-logfile', consts.DEFAULT_RESTAPI_LOG_FILE
            ]
            run_args += ["""irest:create_app()"""]
            gunicorn_master_proc = None

            def kill_proc(dummy_signum, dummy_frame):
                gunicorn_master_proc.terminate()
                gunicorn_master_proc.wait()
                sys.exit(0)

            try:
                gunicorn_master_proc = subprocess.Popen(run_args)

                signal.signal(signal.SIGINT, kill_proc)
                signal.signal(signal.SIGTERM, kill_proc)
            except Exception as ex:
                logging.exception(ex)

        restutils.set_stopped(False)
        super(RESTServerStarter, self).do_start()

    def do_stop(self):
        # only enable this on production mode in linux
        if self.is_production_mode() and oshelper.is_linux():
            pid_file = consts.DEFAULT_SCRIPT_PATH + '/data/temp/irest.pid'
            while True:
                try:
                    with open(pid_file) as f:
                        gunicorn_master_proc_pid = int(f.read())
                        break
                except IOError:
                    logging.debug("Waiting for gunicorn's pid file to be created.")
                    time.sleep(0.1)

            gunicorn_master_proc = psutil.Process(gunicorn_master_proc_pid)
            gunicorn_master_proc.terminate()
        restutils.set_stopped(True)
        super(RESTServerStarter, self).do_stop()

    def handle_stop_event(self, obj):
        self.stop()
        logging.info("Shutting down REST Service")
