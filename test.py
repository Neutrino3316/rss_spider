"""
To find a better way to use multiprocessing, and logging within different process
"""

import multiprocessing
import logging
from logging.handlers import QueueHandler, QueueListener
import time
import random


class Worker(multiprocessing.Process):

    def __init__(self, worker_id: int):
        multiprocessing.Process.__init__(self)
        self.worker_id = worker_id

    def show_id(self):
        time.sleep(random.uniform(0.1, 0.5))
        print("show_id called, worker_%d" % self.worker_id)
        time.sleep(random.uniform(0.1, 0.5))

    def run(self) -> None:
        self.show_id()


def logger_init():
    queue = multiprocessing.Queue()
    # this is the handler for all log records
    handler = logging.StreamHandler()
    # handler.setFormatter(logging.Formatter("%(levelname)s: %(asctime)s - %(process)s - %(message)s"))
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(filename)s:%(lineno)d PID:%(process)d %(name)s \t %(message)s"
    ))

    # queue_listener gets records from the queue and sends them to the handler
    queue_listener = logging.handlers.QueueListener(queue, handler)
    queue_listener.start()

    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    # add the handler to the logger so records from this process are handled
    logger.addHandler(handler)

    return queue_listener, queue


if __name__ == '__main__':

    queue_listener, queue = logger_init()

    logger = logging.getLogger("main.root")
    logger.info("logging from main, starting.")

    worker_num = 7
    worker_list = []
    for i in range(worker_num):
        worker_list.append(Worker(i))

    for worker in worker_list:
        worker.start()

    for worker in worker_list:
        worker.run()

    for worker in worker_list:
        worker.join()

    # show in one process
    # for worker in worker_list:
    #     worker.show_id()

    # show in multiprocess
    # pool = multiprocessing.Pool(worker_num)
    # for worker in worker_list:
    #     pool.apply_async(worker.show_id)
    # pool.close()
    # pool.join()
    # queue_listener.stop()

    logger.info("logging from main, everything ended.")