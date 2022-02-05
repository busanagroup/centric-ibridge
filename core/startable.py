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
from threading import RLock


class StartableListener(object):
    """A Listener support class to provide bridge of state changing behaviour on Startable Object"""

    def __init__(self, starting_func=None, started_func=None, failure_func=None, stopping_func=None, stopped_func=None, configuring_func=None,
                 configured_func=None):
        """
        Initialize the listener
        @param starting_func: callback function when fired upon observable object starting
        @param started_func: callback function when fired upon observable object started
        @param failure_func: callback function when fired upon observable object failure
        @param stopping_func: callback function when fired upon observable object stopping
        @param stopped_func: callback function when fired upon observable object stopped
        @param configuring_func: callback function when fired upon observable object configuring
        @param configured_func: callback function when fired upon observable object configured
        """
        self._starting = starting_func
        self._started = started_func
        self._failure = failure_func
        self._stopping = stopping_func
        self._stopped = stopped_func
        self._configuring = configuring_func
        self._configured = configured_func

    def on_starting(self, obj):
        """Facilitating to notify observer upon starting event"""
        self._starting(obj) if self._starting else None

    def on_started(self, obj):
        """Facilitating to notify observer upon started event"""
        self._started(obj) if self._started else None

    def on_failure(self, obj, exc):
        """Facilitating to notify observer upon failure event"""
        self._failure(obj, exc) if self._failure else None

    def on_stopping(self, obj):
        """Facilitating to notify observer upon stopping event"""
        self._stopping(obj) if self._stopping else None

    def on_stopped(self, obj):
        """Facilitating to notify observer upon stopped event"""
        self._stopped(obj) if self._stopped else None

    def on_configuring(self, obj, config):
        """Facilitating to notify observer upon configuring event"""
        self._configuring(obj, config) if self._configuring else None

    def on_configured(self, obj, config):
        """Facilitating to notify observer upon configured event"""
        self._configured(obj, config) if self._configured else None


class Startable(object):
    """An Abstract Class for generic startable component"""

    FAILED, STOPPED, STARTING, STARTED, STOPPING, CONFIGURING, CONFIGURED, UNCONFIGURED = -1, 0, 1, 2, 3, 4, 5, 6

    def __init__(self, config=None):
        """Initialize the component, configuration object is optional which could be added by set_configuration later"""
        self._state = Startable.STOPPED
        self._configured = Startable.UNCONFIGURED
        self._enabled = True
        self._listeners = list()
        self._lock = RLock()
        self._configuration = config

    def do_start(self):
        """An abstract method to perform component start routines"""
        pass

    def do_stop(self):
        """An abstract method to perform component srtop routines"""
        pass

    def do_configure(self):
        """An abstract method to perform component configuring routines"""
        pass

    def is_enabled(self) -> bool:
        """
        Check if the component is enable
        @return: boolean value
        """
        return self._enabled

    def is_started(self) -> bool:
        """
        Check if the component is started
        @return: boolean value
        """
        return self._state == Startable.STARTED

    def is_starting(self) -> bool:
        """
        Check if the component is starting
        @return: boolean value
        """
        return self._state == Startable.STARTING

    def is_stopped(self) -> bool:
        """
        Check if the component is stopped
        @return: boolean value
        """
        return self._state == Startable.STOPPED

    def is_stopping(self) -> bool:
        """
        Check if the component is stopping
        @return: boolean value
        """
        return self._state == Startable.STOPPING

    def is_running(self) -> bool:
        """
        Ceck if the component is running
        @return: boolean value
        """
        return self.is_started() or self.is_starting()

    def get_configuration(self) -> dict:
        """
        Get the configuration object commonly rfequired upon configuring component
        @return:
        """
        return self._configuration

    def set_configuration(self, config):
        """Set the configuration dictionary commonly required upon configuring this component"""
        self._configuration = config

    def add_listener(self, listener):
        """Add listener to this observable component"""
        self._listeners.append(listener) if isinstance(listener, StartableListener) else None

    def remove_listener(self, listener):
        """Remove listener from this observable component"""
        if isinstance(listener, StartableListener) and (listener in self._listeners):
            obj_pos = self._listeners.index(listener)
            self._listeners.pop(obj_pos)

    def configure(self):
        """Perform configuring this component"""
        self._lock.acquire(blocking=True)
        try:
            if (self._configured == Startable.CONFIGURED) or \
                    (self._state in [Startable.CONFIGURED, Startable.CONFIGURING]):
                return
            self._set_configuring()
            self.do_configure()
            self._set_configured()
        except Exception as exc:
            self._set_failed(exc)
            raise exc
        finally:
            self._lock.release()

    def start(self):
        """Perform Starting this component"""
        self.configure() if self._configured == Startable.UNCONFIGURED else None
        self._lock.acquire(blocking=True)
        try:
            if (not self._enabled) or (self._state in [Startable.STARTED, Startable.STARTING]):
                return
            logging.info("{} - Started".format(self.__class__.__name__))
            self._set_starting()
            self.do_start()
            self._set_started()
        except Exception as exc:
            self._set_failed(exc)
            raise exc
        finally:
            self._lock.release()

    def stop(self):
        """Perform Stopping this component"""
        self._lock.acquire(blocking=True)
        try:
            if self._state in [Startable.STOPPED, Startable.STOPPING]:
                return
            self._set_stopping()
            self.do_stop()
            self._set_stopped()
            logging.info("{} - Stopped".format(self.__class__.__name__))
        except Exception as exc:
            self._set_failed(exc)
            raise exc
        finally:
            self._lock.release()

    def get_listeners(self) -> list:
        """
        get subscribed listener

        @return: list of subscribed listeners
        """
        return self._listeners

    def _set_configured(self):
        self._state = Startable.CONFIGURED
        self._configured = self._state
        for listener in self._listeners:
            listener.on_configured(self, self._configuration)

    def _set_configuring(self):
        self._state = Startable.CONFIGURING
        self._configured = self._state
        for listener in self._listeners:
            listener.on_configuring(self, self._configuration)

    def _set_failed(self, exc):
        self._state = Startable.FAILED
        for listener in self._listeners:
            listener.on_failure(self, exc)

    def _set_starting(self):
        self._state = Startable.STARTING
        for listener in self._listeners:
            listener.on_starting(self)

    def _set_started(self):
        self._state = Startable.STARTED
        for listener in self._listeners:
            listener.on_started(self)

    def _set_stopping(self):
        self._state = Startable.STOPPING
        for listener in self._listeners:
            listener.on_stopping(self)

    def _set_stopped(self):
        self._state = Startable.STOPPED
        for listener in self._listeners:
            listener.on_stopped(self)


class StartableManager(Startable):

    def __init__(self, config=None):
        super(StartableManager, self).__init__(config=config)
        self._startable_objects = list()
        self._lock = RLock()

    def get_objects(self):
        return self._startable_objects

    def get_object(self, cls):
        if not cls:
            return
        for item in self._startable_objects:
            if isinstance(item, cls):
                return item

    def add_object(self, obj):
        if (not obj) or (not isinstance(obj, Startable)):
            return
        if obj not in self._startable_objects:
            self._startable_objects.append(obj)

        try:
            if self.is_running():
                obj.set_configuration(self.get_configuration())
                obj.start()
        except Exception as exc:
            raise RuntimeError(exc)

    def remove_object(self, obj):
        if (not obj) or (not isinstance(obj, Startable)):
            return
        if obj in self._startable_objects:
            obj_pos = self._startable_objects.index(obj)
            self._startable_objects.pop(obj_pos)

    def do_configure(self):
        for item in self._startable_objects:
            try:
                item.set_configuration(self.get_configuration())
                item.configure()
            except Exception as exc:
                logging.error(exc)

    def do_start(self):
        for item in self._startable_objects:
            try:
                item.start()
            except Exception as exc:
                logging.error(exc)

    def do_stop(self):
        for item in self._startable_objects:
            try:
                item.stop()
            except Exception as exc:
                logging.error(exc)


class LifeCycleManager(StartableManager):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    @classmethod
    def get_default_instance(cls):
        cls.SINGLETON_LOCK.acquire(blocking=True)
        try:
            if cls.VM_DEFAULT is None:
                cls.VM_DEFAULT = object.__new__(cls)
                cls.VM_DEFAULT.__init__()

            return cls.VM_DEFAULT
        finally:
            cls.SINGLETON_LOCK.release()