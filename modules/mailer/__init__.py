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
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.msgobject import mq_command
from core.prochandler import CommandProcessor


class MailSender(CommandProcessor):

    __module_name__ = 'COMMON@MAILER'

    def __init__(self):
        super(MailSender, self).__init__()
        prop = self.get_module_configuration()
        self._props = prop[self.__module_name__] if self.__module_name__ in prop else dict()
        self._smtp_host = None
        self._smtp_port = None
        self._smtp_from = None
        self._smtp_user = None
        self._smtp_pass = None
        self._smtp_ssl = False
        self._mailer = None

    def do_configure(self):
        super(MailSender, self).do_configure()
        self._smtp_host = self.get_property_value(self._props, "MAIL_SMTP_HOST", "127.0.0.1")
        self._smtp_port = self.get_property_value(self._props, "MAIL_SMTP_PORT", "25")
        self._smtp_from = self.get_property_value(self._props, "MAIL_SMTP_FROM", "")
        self._smtp_user = self.get_property_value(self._props, "MAIL_SMTP_USER", "")
        self._smtp_pass = self.get_property_value(self._props, "MAIL_SMTP_PASSWORD", "")
        ssl = self.get_property_value(self._props, "MAIL_SMTP_SSL", "false")
        self._smtp_ssl = ssl.lower() == "true"
        self._mailer = smtplib.SMTP_SSL(self._smtp_host, self._smtp_port) if self._smtp_ssl \
            else smtplib.SMTP(self._smtp_host, self._smtp_port)

    @mq_command
    def sendmail(self, mail_to, mail_subject, mail_body, mime_type='text'):
        assert mail_to, "mail_to could not be empty"
        assert mail_subject, "mail_subject could not be empty"
        assert mail_body, "mail_body could not be empty"
        mime_type = mime_type.lower() if mime_type else "text"
        message_header = MIMEMultipart('alternative')
        message_header['Subject'] = mail_subject
        message_header['From'] = self._smtp_from
        message_header['To'] = mail_to
        message_header.attach(MIMEText(mail_body, mime_type))
        self._mailer.ehlo()
        if self._smtp_ssl:
            context = ssl.create_default_context()
            self._mailer.starttls(context=context)
            self._mailer.ehlo()
        self._mailer.login(self._smtp_user, self._smtp_pass)
        try:
            return_val = self._mailer.sendmail(self._smtp_from, mail_to, message_header.as_string())
            if bool(return_val):
                for key in return_val:
                    logging.error("fail to send mail to {0} reason: {1}".format(key, return_val[key]))
        except Exception as ex:
            logging.error(traceback.format_exc(ex))
        finally:
            self._mailer.quit()



