import os.path
import time
from threading import Thread, Lock, Event
from common.error import *
from backend.models import Backup, Node
from common.backup_request import BackupRequest, ForwardRequest
from backend.config import config, log
from common import utils

class Action:
    MAX_RETRY = 5

    def __init__(self):
        self._error_count = 0
        self._min_time_exec = 0
        pass

    def clone(self):
        raise NotImplemented

    def get_min_time_exec(self) -> float:
        return self._min_time_exec

    def set_error_count(self, n : int, min_time : float = 0):
        self._error_count=n
        self._min_time_exec = time.time() + min_time
        return self

    def get_error_count(self):
        return self._error_count

    def is_valid(self)  -> bool:
        #todo
        return True

    def run(self) -> None:
        raise NotImplemented()

class ActionForward(Action):

    def __init__(self, selfurl : str, bid : int, nid : int):
        assert(isinstance(selfurl, str))
        assert(isinstance(bid, int))
        assert(isinstance(nid, int))

        super().__init__()
        self.self_url = selfurl if selfurl[-1] == '/' else (selfurl+"/")
        self.backupid = bid
        self.nodeid = nid

    def clone(self):
        return ActionForward(self.self_url, self.backupid, self.nodeid)\
            .set_error_count(self.get_error_count()+1, 5)

    def get_token(self, backup : Backup, node : Node) -> SSDError:
        assert(isinstance(backup, Backup))
        assert(isinstance(node, Node))

        fwr = ForwardRequest(backup, self.self_url)
        return node.post("/node/forward/request", data=fwr.json())


    def upload(self, node : Node, file : str, token : str) -> SSDError:
        assert(isinstance(file, str))
        assert(os.path.isfile(file))
        assert(isinstance(token, str))

        headers = {
            "X-upload-token": token
        }
        files = {
            "archive": open(file, "rb")
        }
        return node.post("/node/forward", files=files, headers=headers)


    def run(self) -> SSDError:
        backup = Backup.objects.get(id=self.backupid)
        node = Node.objects.get(id=self.nodeid)

        res = self.get_token(backup, node)

        if res.err():
            log.error(str(res))
            return res

        token = res["token"]
        res = self.upload(node, backup.path, token)

        if res.err():
            log.error(str(res))

        return res

class ActionRotateBackup(Action):

    def __init__(self, site, name):
        super().__init__()
        self.site = site
        self.name = name

    def clone(self):
        return ActionRotateBackup(self.site, self.name)\
            .set_error_count(self.get_error_count()+1)

    def run(self) -> SSDError:
        #todo
        return SSDE_OK()



class Qeue(list):
    def __init__(self, size=2048):
        super().__init__([None for i in range(size)])
        self.head=0
        self.tail=0
        self.size=size
        self.lock = Lock()
        self._interrupt = Event()

    def interrupt(self):
        self._interrupt.set()

    def dequeue(self) -> Action:
        while True:
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
            if data.get_min_time_exec()>time.time():
                with self.lock:
                    is_empty = (self.tail==self.head)
                self.enqueue(data)
                if is_empty:
                    time.sleep(0.1)
            else:
                return data





    def enqueue(self, x : (Action, None))  -> None:
        assert(isinstance(x, Action))
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



def interrupt_sleep(signo, frame):
    Scheduler.get_instance().interrupt_sleep()

class Scheduler(Thread):
    _INSTANCE=None

    def __init__(self):
        super().__init__()
        self.lock = Lock()
        self.queue = Qeue()
        self._stop = False

    @staticmethod
    def get_instance():
        if not Scheduler._INSTANCE:
            Scheduler._INSTANCE=Scheduler()
        return Scheduler._INSTANCE

    def stop(self) -> None:
        self.queue.enqueue(None)

    def interrupt_sleep(self):
        self.queue.interrupt()

    def run(self) -> None:
        while True:
            object = self.queue.dequeue()
            if object is None: return
            ret = object.run()
            if ret.ok():
                pass
            else:
                log.error("L'action n'a pu être effectuée (essai: %d)" % object.get_error_count())
                if object.get_error_count()<Action.MAX_RETRY:
                    self.queue.enqueue(object.clone())
                    log.info("L'action a été réinjecté dans la file")
                else:
                    log.critical("L'action a atteint la limite d'essai maximum... Abandon")



    def forward(self, self_url : str, backup : Backup, node : Node) -> None:
        assert(isinstance(self_url, str))
        assert(isinstance(backup, Backup))
        assert(isinstance(node, Node))
        self.queue.enqueue(ActionForward(self_url, backup.id, node.id))

    def rotate_backup(self, bc : Backup) -> None:
        assert(isinstance(bc, Backup))
        self.queue.enqueue(ActionRotateBackup(bc.site, bc.backup_name))

def init() -> None:
    pass
    inst = Scheduler.get_instance()
    inst.start()

def forward_backup(self_url : str, bc : Backup, node : Node = None) -> None:
    inst = Scheduler.get_instance()
    if node is None:
        for node in bc.forward_left.all():
            inst.forward(self_url, bc, node)
    elif isinstance(node, Node):
        inst.forward(self_url, bc, node)
    else:
        assert(False)

def rotate_backup(bc : Backup) -> None:
    inst = Scheduler.get_instance()
    inst.rotate_backup(bc)
