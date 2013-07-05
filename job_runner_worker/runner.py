import logging
import signal
import sys

import gevent
import gevent.pool
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

    gevent_pool = gevent.pool.Group()
    reset_incomplete_runs()
    concurrent_jobs = config.getint('job_runner_worker', 'concurrent_jobs')

    run_queue = Queue()
    kill_queue = Queue()
    event_queue = Queue()
    exit_queue = JoinableQueue()
    event_exit_queue = Queue()

    # callback for SIGTERM
    def terminate_callback(*args, **kwargs):
        logger.warning('Worker is going to terminate!')
        for i in range(concurrent_jobs + 2):
            # we don't want to kill the event greenlet, since we want to
            # publish events of already running jobs
            exit_queue.put(None)

    # callback for when an exception is raised in a execute_run greenlet
    def recover_run(greenlet):
        logger.warning(
            'Recovering execute_run greenlet which raised: {0}'.format(
                greenlet.exception))
        gevent_pool.spawn(
            execute_run,
            run_queue,
            event_queue,
            exit_queue,
        ).link_exception(recover_run)

    # callback for when an exception is raised in enqueue_actions greenlet
    def recover_enqueue_actions(greenlet):
        logger.warning(
            'Recovering enqueue_actions greenlet which raised: {0}'.format(
                greenlet.exception))
        gevent_pool.spawn(
            enqueue_actions,
            context,
            run_queue,
            kill_queue,
            event_queue,
            exit_queue,
        ).link_exception(recover_enqueue_actions)

    # callback for when an exception is raised in kill_run greenlet
    def recover_kill_run(greenlet):
        logger.warning(
            'Recovering kill_run greenlet which raised: {0}'.format(greenlet))
        gevent_pool.spawn(
            kill_run,
            kill_queue,
            event_queue,
            exit_queue,
        ).link_exception(recover_kill_run)

    # start the enqueue_actions greenlet
    gevent_pool.spawn(
        enqueue_actions,
        context,
        run_queue,
        kill_queue,
        event_queue,
        exit_queue,
    ).link_exception(recover_enqueue_actions)

    # start the execute_run greenlets
    for x in range(concurrent_jobs):
        gevent_pool.spawn(
            execute_run,
            run_queue,
            event_queue,
            exit_queue,
        ).link_exception(recover_run)

    # start the kill_run greenlet
    gevent_pool.spawn(
        kill_run,
        kill_queue,
        event_queue,
        exit_queue
    ).link_exception(recover_kill_run)

    # start the publish (event publisher) greentlet
    publisher_loop = gevent.spawn(
        publish, context, event_queue, event_exit_queue)

    # catch SIGTERM signal
    signal.signal(signal.SIGTERM, terminate_callback)

    # wait for all the greenlets to complete in this group
    gevent_pool.join()

    # now terminate the event queue. this one should be terminated at the
    # end, since we want all events to be published.
    event_exit_queue.put(None)
    publisher_loop.join()
    sys.exit('Worker terminated')
