import logging
import sys

import gevent
import zmq.green as zmq
from gevent.queue import Queue

from job_runner_worker.cleanup import reset_incomplete_runs
from job_runner_worker.config import config
from job_runner_worker.enqueuer import enqueue_runs
from job_runner_worker.events import publish
from job_runner_worker.worker import execute_run


logger = logging.getLogger(__name__)


def run():
    """
    Start consuming runs and executing them.
    """
    context = zmq.Context(1)

    greenlets = []
    reset_incomplete_runs()
    concurrent_jobs = config.getint('job_runner_worker', 'concurrent_jobs')

    run_queue = Queue(concurrent_jobs)
    event_queue = Queue()

    greenlets.append(
        gevent.spawn(enqueue_runs, context, run_queue, event_queue))

    for x in range(concurrent_jobs):
        greenlets.append(gevent.spawn(execute_run, run_queue, event_queue))

    greenlets.append(gevent.spawn(publish, context, event_queue))

    try:
        for greenlet in greenlets:
            greenlet.join()
    except KeyboardInterrupt:
        sys.exit()

    context.term()
    sys.exit('Something went wrong, all greenlets died!')
