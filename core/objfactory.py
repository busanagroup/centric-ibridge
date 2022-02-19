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
from core.configurable import Configurable
from utils import oshelper


class AbstractFactory(Configurable):

    def __init__(self, config=None):
        super(AbstractFactory, self).__init__(config=config)

    def create_object(self, name, **kwargs):
        pass

    @staticmethod
    def import_klass(class_name):
        components, import_module = oshelper.extract_class_name(class_name)
        mod = __import__(import_module)
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    @staticmethod
    def create_instance(klass):
        instance = object.__new__(klass)
        instance.__init__()
        return instance




