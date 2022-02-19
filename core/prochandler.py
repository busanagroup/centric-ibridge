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
from core import msgobject
from core.configurable import Configurable


class BaseCommandProcessor(Configurable):

    def __init__(self, config=None):
        super(BaseCommandProcessor, self).__init__(config=config)
        self._parent = None
        self._module_config = None
        self._message_object = None

    @classmethod
    def get_module_name(cls):
        return getattr(cls, '__module_name__') if hasattr(cls, '__module_name__') else None

    def _is_mq_method(self, func_name, func_code=None, mq_type=msgobject.MODE_COMMAND):
        """Check if function is a published method"""
        func = getattr(self, func_name, None) if func_code is None else func_code
        return True if (func is not None) and (getattr(func, 'mq_type', msgobject.MODE_COMMAND) == mq_type) else False

    def perform_execute(self, message_obj, cmd_func=None):
        execution_type = msgobject.MODE_EVENT if cmd_func else msgobject.MODE_COMMAND
        func_name = message_obj.COMMAND if execution_type == msgobject.MODE_COMMAND else cmd_func
        if func_name not in [None, '']:
            queue_func = getattr(self, func_name, None)
            if queue_func and self._is_mq_method(func_name, queue_func, execution_type):
                _args, _kwargs = message_obj.PARAMS
                logging.debug("executing {0}".format(func_name))
                return queue_func(*_args, **_kwargs)
        return None

    def set_parent(self, parent):
        self._parent = parent

    def get_parent(self):
        return self._parent

    def set_module_configuration(self, module_config):
        self._module_config = module_config

    def get_module_configuration(self):
        return self._module_config

    def get_message_object(self):
        return self._message_object

    def set_message_object(self, message_object):
        self._message_object = message_object


class CommandProcessor(BaseCommandProcessor):

    def __init__(self, config=None):
        super(CommandProcessor, self).__init__(config=config)

    @staticmethod
    def get_property_value(prop, key, default):
        ret_val = prop[key] if key in prop else default
        ret_val = ret_val if ret_val else default
        return ret_val

