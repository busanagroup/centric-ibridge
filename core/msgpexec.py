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
try:
    import ujson as json
except:
    import json

try:
    import pybase64 as base64
except:
    import base64

import time
import logging
import multiprocessing as mp
from multiprocessing.pool import Pool
from queue import Empty
from common.msgobject import AbstractMessage
from core.msgexec import BaseExecutor, ModuleExecutor, MessageExecutionManager


class ShutdownMessage(AbstractMessage):
    def __init__(self):
        super(ShutdownMessage, self).__init__(msg_type=999)

    def encode(self):
        if self.PARAMS is None:
            self.PARAMS = [list(), dict()]
        adict = {'msgtype': self.message_mode,
                 'msgid': self.MESSAGE_ID,
                 'module': self.MODULE,
                 'submodule': self.SUBMODULE,
                 'data': self.PARAMS,
                 'options': self.options.copy()}
        command_str = json.dumps(adict)
        return base64.b64encode(command_str.encode("utf-8"))


class ProcessExecutor(ModuleExecutor):

    def __init__(self, config=None, module=None, workers=16):
        super(ProcessExecutor, self).__init__(config=config, module=module, workers=workers)

    def do_start(self):
        self._pool = Pool(processes=self._max_processes)


class BaseProcessExecutor(BaseExecutor):

    def __init__(self, config=None, module_config=None, module=None):
        super(BaseProcessExecutor, self).__init__(config=config, module_config=module_config, module=module)
        self._process = None

    def do_configure(self):
        super(BaseProcessExecutor, self).do_configure()
        self._process = mp.Process(target=self.subprocess_entry)
        
    def do_start(self):
        super(BaseProcessExecutor, self).do_start()
        self._process.start()

    def do_stop(self):
        super(BaseProcessExecutor, self).do_stop()
        self._process.terminate()

    def subprocess_entry(self):
        raise NotImplementedError()


class ProcessThreadExecutor(BaseProcessExecutor):
    """
    Process based message execution manager
    """

    def __init__(self, config=None, module=None, workers=16):
        super(ProcessThreadExecutor, self).__init__(config=config, module=module)
        self._queue = None
        self._max_processes = workers

    def do_configure(self):
        super(ProcessThreadExecutor, self).do_configure()
        self._queue = mp.Queue()

    def do_stop(self):
        self.submit_task(ShutdownMessage())
        super(ProcessThreadExecutor, self).do_stop()

    def submit_task(self, message_obj: AbstractMessage):
        self._queue.put(message_obj)

    def subprocess_entry(self):
        _handler = ModuleExecutor(self.get_configuration(), self.get_module(), self._max_processes)
        _handler.set_properties(self.get_command_properties(), self.get_event_properties())
        _handler.set_module_configuration(self.get_module_configuration())
        _handler.configure()
        _handler.start()
        try:
            while True:
                try:
                    message_obj = self._queue.get(True, 0.1)
                    if message_obj:
                        try:
                            if isinstance(message_obj, ShutdownMessage):
                                break
                            elif isinstance(message_obj, AbstractMessage):
                                _handler.execute_module(message_obj)
                        except Exception as ex:
                            logging.exception(ex)
                except Empty:
                    time.sleep(0.1)
        finally:
            _handler.stop()


class ProcessMessageExecutionManager(MessageExecutionManager):

    def __init__(self, config, klass=ProcessThreadExecutor):
        super(ProcessMessageExecutionManager, self).__init__(config=config, klass=klass)
