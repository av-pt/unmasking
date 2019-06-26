# Copyright (C) 2017-2019 Janek Bevendorff, Webis Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from authorship_unmasking.event.interfaces import EventHandler

import asyncio
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import current_process, Event, JoinableQueue, Lock
from queue import Empty
from threading import current_thread
from typing import Set


class EventBroadcaster:
    """
    Global event broadcaster to send and receive events across threads and processes.
    Instances of this class are singletons bound to the current thread.
    """

    _lock = Lock()
    _instances = {}

    def __new__(cls, instance=None):
        """
        :param instance: instance identifier (defaults to current thread name)
        """
        if instance is None:
            instance = current_thread().name

        with cls._lock:
            if instance not in cls._instances:
                cls._instances[instance] = cls._EventBroadcaster.__new__(cls._EventBroadcaster)
                cls._instances[instance].__init__(instance)

            return cls._instances[instance]

    @classmethod
    def teardown(cls, instance=None):
        """
        Tear down event handling for this thread or another specific instance.
        This method is thread-safe.

        :param instance: instance name to tear down (defaults to current thread)
        """

        if instance is None:
            instance = current_thread().name

        with EventBroadcaster._lock:
            if instance in EventBroadcaster._instances:
                del EventBroadcaster._instances[instance]

    class _EventBroadcaster:
        def __init__(self, instance_id):
            self.__subscribers = {}
            self._instance_id = instance_id

        def subscribe(self, event_name: str, handler: EventHandler, senders: Set[type] = None):
            """
            Subscribe to events with the name `event_name`.
            When the event is fired, all subscribed :class:`EventHandler`s will be notified
            by calling their :method:`EventHandler.handle()` method.

            :param event_name: string identifier of the event to subscribe to
            :param handler: event handler
            :param senders: senders to listen to (None to subscribe to events from all senders)
            """
            if event_name not in self.__subscribers:
                self.__subscribers[event_name] = []

            event_pair = (senders, handler)
            if event_pair not in self.__subscribers[event_name]:
                self.__subscribers[event_name].append((senders, handler))

        def unsubscribe(self, event_name: str, handler, senders: Set[type] = None):
            """
            Unsubscribe `handler` from the given event.

            :param event_name: string identifier of the event to unsubscribe from
            :param handler: event handler to unsubscribe
            :param senders: set of senders (must be the same set that was used to subscribe to the event)
            """
            if event_name not in self.__subscribers:
                return

            for e in self.__subscribers:
                self.__subscribers[e] = [i for i in self.__subscribers[e] if i != (senders, handler)]

        async def publish(self, event_name: str, event: Event, sender: type):
            """
            Publish the given event and notify all subscribed :class:`EventHandler`s.
            This method is thread-safe. If this method is called from a worker process,
            calls will be delegated to the main process.

            :param event_name: name of this event (e.g. 'onProgress')
                               The name can be freely chosen, but should start with 'on' and
                               use camelCasing to separate words
            :param event: event to publish, which must have its :attr:`Event.name` property set
            :param sender: ``__class__`` type object of the sending class or object
            """

            if not MultiProcessEventContext().initialized:
                raise RuntimeError("Cannot publish without initialized MultiProcessingContext")

            if current_process().name != MultiProcessEventContext().main_process_name \
                    or current_thread().name != MultiProcessEventContext().main_thread_name:

                if MultiProcessEventContext().terminate_event.is_set():
                    # application is about to terminate, don't accept any new events from workers
                    return

                # We are in a worker process, delegate events to main process
                MultiProcessEventContext().queue.put((event_name, event, sender))
                return

            if event_name not in self.__subscribers:
                return

            for h in self.__subscribers[event_name]:
                if h[0] is None or sender in h[0]:
                    await h[1].handle(event_name, event, sender)


class MultiProcessEventContext:
    """
    Context manager for multiprocess event communication.
    Use this in an async with statement around any multiprocessing or multi threading
    code to ensure events are properly delegated to the main process / thread.

    You should make sure to "await" as soon as possible after creating the
    context to allow the initializing code to be executed.

    Please note that due to internal queueing, the managing (main) process will not exit until
    cleanup() is called. Therefore a MultiProcessingEventContext always must be inside any
    ::class: ProcessPoolExecutor() context manager or else the program execution will hang.

    Instances of this class are singletons bound to the current thread.
    """

    _lock = Lock()
    _instances = {}

    def __new__(cls, instance=None):
        """
        :param instance: instance identifier (defaults to current thread name)
        """
        if instance is None:
            instance = current_thread().name

        with cls._lock:
            if instance not in cls._instances:
                cls._instances[instance] = cls._MultiProcessEventContext.__new__(cls._MultiProcessEventContext)
                cls._instances[instance].__init__(instance)

            return cls._instances[instance]

    class _MultiProcessEventContext:

        def __init__(self, instance_id):
            self.main_process_name = None
            self.main_thread_name = None
            self.initialized = False

            self.terminate_event = Event()
            self.queue = JoinableQueue()

            self._instance_id = instance_id

        async def start(self):
            """
            Initialize event queue consumer thread for multiprocess event handling.
            """
            if self.initialized:
                raise RuntimeError("Nested MultiProcessEventContexts are not supported")

            self.main_process_name = current_process().name
            self.main_thread_name = current_thread().name

            self.terminate_event.clear()
            self.initialized = True

            asyncio.ensure_future(self.__await_queue())

            # allow queue polling loop to initialize
            await asyncio.sleep(0)

        async def cleanup(self):
            """
            Cleanup method to ensure all event queues are cleared and worker processes
            are signaled to shut down.
            """

            self.terminate_event.set()

            # wait for remaining events to be processes before exiting the context
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)

            await loop.run_in_executor(executor, self.queue.join)

            try:
                while not self.queue.empty():
                    self.queue.get(False)
            except Empty:
                pass

            # quit any workers still waiting for the queue
            self.queue.put(None)

            while not MultiProcessEventContext().queue.empty():
                self.queue.get(False)

            EventBroadcaster.teardown(self._instance_id)
            with MultiProcessEventContext._lock:
                if self._instance_id in MultiProcessEventContext._instances:
                    del MultiProcessEventContext._instances[self._instance_id]

            self.initialized = False

        async def __await_queue(self):
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)

            while loop.is_running():
                f = loop.run_in_executor(executor, self.queue.get, True)

                await f
                self.queue.task_done()

                if f.result() is None:
                    return

                await EventBroadcaster().publish(*f.result())

        async def __aenter__(self):
            """
            Initialize event queue consumer thread for multiprocess event handling.
            """
            await self.start()
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """
            Process any remaining events and signal queue consumer thread to exit.
            """
            await self.cleanup()