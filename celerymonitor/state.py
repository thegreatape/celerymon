import time
from collections import defaultdict
from datetime import datetime

HEARTBEAT_EXPIRE = 120 # Heartbeats must be at most 2 minutes apart.


class MonitorState(object):

    def __init__(self):
        self.hearts = {}
        self.tasks = defaultdict(lambda: defaultdict(lambda: 0))
        self.workers = defaultdict(lambda: {'jobs': defaultdict(lambda: 0)})

    # ---------------
    # event recievers
    # ---------------
    def receive_worker_event(self, event):
        #self.workers[event["hostname"]]
        pass

    def receive_task_event(self, event):
        if event['type'] == 'task-received':
            self.tasks[event['name']][event['type']] += 1

    def receive_heartbeat(self, event):
        self.hearts[event["hostname"]] = event["timestamp"]

    def receive_task_received(self, event):
        self.workers[event["hostname"]]['jobs'][event["name"]] += 1

    # ---------------------
    # informational methods
    # ---------------------
    def tasks_by_type(self):
        t = defaultdict(lambda: [])
        for id, events in self.task_events.items():
            try:
                task_type = self.tasks[id]["name"]
            except KeyError:
                pass
            else:
                t[task_type].append(id)
        return t

    def get_task_info(self, task_id):
        task_info = dict(self.tasks[task_id])

        task_events = []
        for event in self.task_events[task_id]:
            if event["state"] in ("task-failed", "task-retried"):
                task_info["exception"] = event["exception"]
                task_info["traceback"] = event["traceback"]
            elif event["state"] == "task-succeeded":
                task_info["result"] = event["result"]
            task_events.append({event["state"]: event["when"]})
        task_info["events"] = task_events

        return task_info

    def timestamp_to_isoformat(self, timestamp):
        return datetime.fromtimestamp(timestamp).isoformat()

    def list_workers(self):
        alive_workers = []
        for hostname, events in self.workers.items():
            if events[-1]["state"] == "worker-online":
                alive_workers.append({hostname: events[-1]["when"]})
        return alive_workers

    def list_worker_tasks(self, hostname):
        alive_workers = self.list_workers()
        tasks_for_worker = defaultdict(lambda: [])
        for hostname, when in alive_workers.items():
            for task_id, task_info in self.tasks:
                if task_info["hostname"] == hostname:
                    tasks_for_worker[hostname].append(task_id)
        return tasks_for_worker

    def worker_is_alive(self, hostname):
        last_worker_event = self.workers[hostname][-1]
        if last_worker_event and last_worker_event == "worker-online":
            time_of_last_heartbeat = self.hearts[hostname]
            if time.time() < time_of_last_heartbeat + HEARTBEAT_EXPIRE:
                return True
        return False

    def tasks_by_time(self):
        pass
    
    def tasks_by_last_state(self):
        return [events[-1] for event in self.task_by_time()]

monitor_state = MonitorState()
