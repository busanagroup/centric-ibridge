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


class Configurable(object):
    CONFIGURING, CONFIGURED, UNCONFIGURED = 4, 5, 6

    def __init__(self, config=None):
        """Initialize the component, configuration object is optional which could be added by set_configuration later"""
        self._configuration = config
        self._configured = Configurable.UNCONFIGURED
        self._lock = RLock()

    def do_configure(self):
        """An abstract method to perform component configuring routines"""
        pass

    def is_configured(self) -> bool:
        return self._configured != Configurable.UNCONFIGURED

    def get_configuration(self) -> dict:
        """
        Get the configuration object commonly rfequired upon configuring component
        @return:
        """
        return self._configuration

    def set_configuration(self, config):
        """Set the configuration dictionary commonly required upon configuring this component"""
        self._configuration = config

    def configure(self):
        """Perform configuring this component"""
        self.lock.acquire(blocking=True)
        try:
            if self._configured == Configurable.CONFIGURED:
                return
            self._set_configuring()
            self.do_configure()
            self._set_configured()
        except Exception as exc:
            raise exc
        finally:
            self.lock.release()

    def get_config_value(self, key, def_value):
        assert self._configuration is not None, "This object has not been configured properly"
        return_val = def_value if key not in self._configuration else self._configuration[key]
        return def_value if return_val in [None, ""] else return_val

    def _set_configured(self):
        self._configured = Configurable.CONFIGURED

    def _set_configuring(self):
        self._configured = Configurable.CONFIGURING

    @property
    def lock(self):
        return self._lock
