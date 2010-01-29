import threading

from carrot.connection import DjangoBrokerConnection
from celery.events import EventReceiver

from celerymonitor.state import monitor_state
from celerymonitor.web import WebServerThread


class MonitorListener(threading.Thread):
    """Capture events sent by messages and store them in memory."""

    def __init__(self, state, *args, **kwargs):
        super(MonitorListener, self).__init__(*args, **kwargs)
        self.connection = DjangoBrokerConnection()
        self.receiver = EventReceiver(self.connection, handlers={
            "task-received": state.receive_task_received,
            "task-accepted": state.receive_task_event,
            "task-succeeded": state.receive_task_event,
            "task-retried": state.receive_task_event,
            "task-failed": state.receive_task_event,
            "worker-online": state.receive_worker_event,
            "worker-offline": state.receive_worker_event,
            "worker-heartbeat": state.receive_heartbeat,
            })
        self.setDaemon(True)

    def run(self):
        self.receiver.capture()


class MonitorService(object):
    """celerymon"""

    def __init__(self, logger, http_port=8989):
        self.logger = logger
        self.http_port = http_port

    def start(self):
        MonitorListener(monitor_state).start()
        WebServerThread(port=self.http_port).start()
