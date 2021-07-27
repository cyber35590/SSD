import time
from threading import Thread, Lock

from backend.models import Backup, Node


class Action:
    def __init__(self):
        pass

    def is_valid(self):
        return True

    def run(self):
        raise NotImplemented()

class ActionForward(Action):

    def __init__(self, bid, nid):
        super().__init__()
        self.backupid = bid
        self.nodeid = nid


    def get_token(self, backup : Backup):
        # todo
        pass

    def upload(self, file : str, token :str):
        # todo
        pass

    def run(self):
        backup = Backup.objects.get(id=self.backupid)
        node = Backup.objects.get(id=self.nodeid)

        res = self.get_token(backup)

        if res.err():
            # todo
            pass

        token = res["token"]
        self.upload(backup.path, token)
        exit(0)
        #todo




class Qeue(list):
    def __init__(self, size=2048):
        super().__init__([None for i in range(50)])
        self.head=0
        self.tail=0
        self.size=size
        self.lock = Lock()

    def dequeue(self):
        while True:
            with self.lock:
                h,t = self.head, self.tail

            if h!=t: # not empty
                break
            else:
                time.sleep(0.01)

        with self.lock:
            data = self[self.tail]
            self.tail = (self.tail + 1) % self.size
        return data


    def enqueue(self, x):
        while True:
            with self.lock:
                h,t, s = self.head, self.tail, self.size

            if h!=((t-1)%s): # not full
                break
            else:
                time.sleep(0.01)

        with self.lock:
            self[self.head] = x
            self.head=(self.head+1)%self.size





class Scheduler(Thread):
    _INSTANCE=None

    @staticmethod
    def get_instance():
        if not Scheduler._INSTANCE:
            Scheduler._INSTANCE=Scheduler()
        return Scheduler._INSTANCE

    def __init__(self):
        super().__init__()
        self.lock = Lock()
        self.queue = Qeue()
        self._stop = False

    def stop(self):
        self.queue.enqueue(None)


    def run(self) -> None:
        while True:
            object = self.queue.dequeue()
            if object is None: return
            object.run()

    def forward(self, backup, node):
        self.queue.enqueue(ActionForward(backup.id, node.id))

def init():
    pass
    inst = Scheduler.get_instance()
    inst.start()

def forward_backup(bc):
    inst = Scheduler.get_instance()
    for node in bc.forward_left.all():
        inst.forward(bc, node)

