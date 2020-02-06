"""
To find a better way to use multiprocessing, and logging within different process
"""

import multiprocessing
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


if __name__ == '__main__':

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
