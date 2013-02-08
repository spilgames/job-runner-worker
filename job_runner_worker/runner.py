import logging
import signal
import sys
import time

import gevent
import zmq.green as zmq
from gevent.queue import JoinableQueue, Queue

from job_runner_worker.cleanup import reset_incomplete_runs
from job_runner_worker.config import config
from job_runner_worker.enqueuer import enqueue_actions
from job_runner_worker.events import publish
from job_runner_worker.worker import execute_run, kill_run


logger = logging.getLogger(__name__)


def run():
    """
    Start consuming runs and executing them.
    """
    context = zmq.Context(1)

    greenlets = []
    reset_incomplete_runs()
    concurrent_jobs = config.getint('job_runner_worker', 'concurrent_jobs')

    run_queue = Queue()
    kill_queue = Queue()
    event_queue = Queue()
    exit_queue = JoinableQueue()
    event_exit_queue = Queue()

    greenlets.append(
        gevent.spawn(
            enqueue_actions,
            context,
            run_queue,
            kill_queue,
            event_queue,
            exit_queue,
        )
    )

    for x in range(concurrent_jobs):
        greenlets.append(gevent.spawn(
            execute_run,
            run_queue,
            event_queue,
            exit_queue,
        ))

    greenlets.append(gevent.spawn(
        kill_run, kill_queue, event_queue, exit_queue))
    greenlets.append(gevent.spawn(
        publish, context, event_queue, event_exit_queue))

    def terminate_callback(*args, **kwargs):
        logger.warning('Worker is going to terminate!')
        for i in range(len(greenlets) - 1):
            # we don't want to kill the event greenlet, since we want to
            # publish events of already running jobs
            exit_queue.put(None)

    signal.signal(signal.SIGTERM, terminate_callback)

    for greenlet in greenlets[:-1]:
        greenlet.join()

    # now terminate the event queue
    event_exit_queue.put(None)
    greenlets[-1].join()
    sys.exit('Worker terminated')
