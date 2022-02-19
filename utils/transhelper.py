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

from utils import oshelper
from core.transport.xsocktransport import UnixSocketTransport
from core.transport.localtransport import LocalhostTransport
from core.transfactory import TransportPreparer


def get_local_transport():
    return UnixSocketTransport.get_default_instance() if not oshelper.is_windows() \
        else LocalhostTransport.get_default_instance()


def get_mq_transport(config, index):
    return TransportPreparer.create_transport(config, index)
