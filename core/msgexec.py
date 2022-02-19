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
from common import consts
from common import modconfig
from core.objfactory import AbstractFactory
from core.startable import Startable, StartableManager
from core.msgobject import MessageFactory, MessageEvent, AbstractMessage
from core.msghandler import MessageNotifier
from core.prochandler import CommandProcessor
from multiprocessing.pool import ThreadPool
from configparser import ConfigParser
from jproperties import Properties
from threading import get_ident


class DummyClass(object):
    pass


class BaseExecutor(Startable):

    def __init__(self, config=None, module_config=None, module=None):
        super(BaseExecutor, self).__init__(config=config)
        self._collection = dict()
        self._module = module
        self._module_config = module_config
        self._command_props = None
        self._event_props = None
        self._module_dict = dict()

    def _get_klass_from_cache(self, class_name):
        return self._module_dict[class_name] if class_name in self._module_dict else None

    def _register_klass_to_cache(self, class_name, mod):
        self._module_dict[class_name] = mod

    def set_module(self, module):
        self._module = module

    def get_module(self):
        return self._module

    def is_valid_module(self, message_obj):
        return message_obj.MODULE == self._module

    def get_command_properties(self):
        return self._command_props

    def get_event_properties(self):
        return self._event_props

    def set_properties(self, cmd_props, event_props):
        self._command_props = cmd_props
        self._event_props = event_props

    def has_service(self, message_obj: AbstractMessage):
        props = self.get_event_properties() if isinstance(message_obj, MessageEvent) \
            else self.get_command_properties()
        return props.has_section(message_obj.get_module_id()) if isinstance(message_obj, MessageEvent) \
            else message_obj.get_module_id() in props.keys()

    def submit_task(self, message_obj):
        raise NotImplementedError()

    def set_module_configuration(self, module_config):
        self._module_config = module_config

    def get_module_configuration(self):
        return self._module_config

    @staticmethod
    def _get_klass_module(msg_obj: AbstractMessage, props):
        class_name = msg_obj if isinstance(msg_obj, str) \
            else props.properties[msg_obj.get_module_id()]
        components = class_name.split(".")
        return components, ".".join(components[:-1]), class_name

    def _get_klass(self, msg_obj: AbstractMessage, props):
        components, import_modules, class_name = self._get_klass_module(msg_obj, props)
        logging.debug("BaseExecutor.get_klass: {0} output {1} - {2}".format(msg_obj, components, import_modules))
        mod = self._get_klass_from_cache(class_name)
        if not mod:
            try:
                mod = __import__(import_modules)
                for cmp in components[1:]:
                    mod = getattr(mod, cmp)
                mod = mod if issubclass(mod, CommandProcessor) else None
                self._register_klass_to_cache(class_name, mod) if mod else None
            except Exception as ex:
                logging.error(ex)
        return mod

    def _create_object(self, klass, message_obj: AbstractMessage):
        if not klass:
            return None
        if klass.__name__ not in self._collection:
            self._collection[klass.__name__] = DummyClass()
        parent = self._collection[klass.__name__]
        module = object.__new__(klass)
        module.__init__()
        module.set_configuration(self.get_configuration())
        module.set_module_configuration(self.get_module_configuration())
        module.set_parent(parent)
        module.set_message_object(message_obj)
        module.configure()
        logging.debug("BaseExecutor.create_object: {0} output {1}".format(klass, module))
        return module

    def _collect_object_module(self, message_obj: AbstractMessage) -> [[object, str]]:
        props = self.get_event_properties() if isinstance(message_obj, MessageEvent) \
            else self.get_command_properties()
        ret_list = list()
        try:
            if isinstance(message_obj, MessageEvent):
                section_props = props[message_obj.get_module_id()]
                str_mod = None if message_obj.EVENT not in section_props else section_props[message_obj.EVENT]
                list_mod = [str_item.split(":") for str_item in (str_mod.split(",") if str_mod else [])]
                for str_mod, str_func in list_mod:
                    klass = self._get_klass(str_mod, section_props)
                    module = self._create_object(klass, message_obj)
                    ret_list.append([module, str_func])
            else:
                klass = self._get_klass(message_obj, props)
                module = self._create_object(klass, message_obj)
                ret_list.append([module, None])
        except Exception as ex:
            logging.exception(ex)
        return ret_list


class ModuleExecutor(BaseExecutor):
    def __init__(self, config=None, module=None, workers=4):
        super(ModuleExecutor, self).__init__(config=config, module=module)
        self._max_processes = workers
        self._pool = None

    def do_configure(self):
        self._max_processes = self._max_processes if self._max_processes > 0 else 4

    def do_start(self):
        self._pool = ThreadPool(processes=self._max_processes)

    def do_stop(self):
        self._pool.terminate()

    def assign_task(self, module: BaseExecutor, message_obj: AbstractMessage, func: str = None):
        self._pool.apply_async(self.do_execute, (module, message_obj, func))

    @staticmethod
    def do_execute(module: CommandProcessor, message_obj: AbstractMessage, func: str):
        logging.debug("Processing {0} on thread {1}".format(message_obj.get_module_id(), get_ident()))
        try:
            module.perform_execute(message_obj, func)
        except Exception as ex:
            logging.exception(ex)
        finally:
            logging.debug("End processing {0} on thread {1}".format(message_obj.get_module_id(), get_ident()))

    def execute_module(self, message_obj: AbstractMessage):
        for module, str_func in self._collect_object_module(message_obj):
            self.assign_task(module, message_obj, str_func)

    def submit_task(self, message_obj: AbstractMessage):
        if self.has_service(message_obj):
            self.execute_module(message_obj)
        else:
            logging.error("Could not parse message correctly")


class ExecutorFactory(AbstractFactory):

    def __init__(self, config=None, klass=None):
        super(ExecutorFactory, self).__init__(config=config)
        self._command_props = None
        self._event_props = None
        self._klass = klass if klass else ModuleExecutor

    def do_configure(self):
        config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.DEFAULT_COMMAND_FILE)
        self._command_props = Properties()
        with open(config_file, "rb") as file_prop:
            self._command_props.load(file_prop, "utf-8")
        config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.DEFAULT_EVENT_FILE)
        self._event_props = ConfigParser()
        self._event_props.read(config_file)

    def generate(self, config, message_obj: AbstractMessage):
        module_obj = object.__new__(self._klass)
        module_obj.__init__()
        if isinstance(module_obj, BaseExecutor):
            module_obj.set_configuration(config)
            module_obj.set_module(message_obj.MODULE)
            module_obj.set_properties(self._command_props, self._event_props)
        return module_obj


class BaseExecutionManager(StartableManager):

    def __init__(self, config, klass):
        super(BaseExecutionManager, self).__init__(config=config)
        self._executor_factory = ExecutorFactory(config=config, klass=klass)
        self._module_config = None

    def do_configure(self):
        self._executor_factory.configure()
        self._module_config = modconfig.get_configuration()

    def get_valid_module(self, message_obj: AbstractMessage):
        object_list = [obj for obj in self.get_objects() if isinstance(obj, BaseExecutor)]
        for module_obj in object_list:
            if module_obj.is_valid_module(message_obj):
                return module_obj
        return None

    def _register_module_object(self, message_obj: AbstractMessage):
        module_object = self._executor_factory.generate(self.get_configuration(), message_obj)
        module_object.set_configuration(self.get_configuration())
        module_object.set_module_configuration(self._module_config)
        self.add_object(module_object if module_object else None)
        return module_object


class MessageExecutionManager(BaseExecutionManager):
    """
    Thread based message execution Manager
    """

    def __init__(self, config, klass=ModuleExecutor):
        super(MessageExecutionManager, self).__init__(config=config, klass=klass)

    def register_listener(self, listener):
        listener.set_on_message_received(self.on_handle_message) if isinstance(listener, MessageNotifier) else None

    def on_handle_message(self, obj, message: str):
        try:
            message_object = MessageFactory.generate(message) if message else None
            if (not message_object) or (not self.is_running()):
                logging.error("Could not parse message correctly: {0}".format(message))
                return
            module_object = self.get_valid_module(message_object)
            module_object = module_object if module_object else self._register_module_object(message_object)
            module_object.submit_task(message_object) if module_object else None
        except Exception as ex:
            logging.exception(ex)
