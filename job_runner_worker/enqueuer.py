import json
import logging
import random
import time
from datetime import datetime, timedelta

import zmq.green as zmq
from gevent.queue import Empty
from pytz import utc

import job_runner_worker
from job_runner_worker.config import config
from job_runner_worker.models import KillRequest, Run, Worker


logger = logging.getLogger(__name__)


def enqueue_actions(
        zmq_context, run_queue, kill_queue, event_queue, exit_queue):
    """
    Handle incoming actions sent by the broadcaster.

    :param zmq_context:
        An instance of ``zmq.Context``.

    :param run_queue:
        An instance of ``Queue`` for pushing the runs to.

    :param kill_queue:
        An instance of ``Queue`` for pushing the kill-requests to.

    :param event_queue:
        An instance of ``Queue`` for pushing events to.

    :param exit_queue:
        An instance of ``Queue`` to consume from. If this queue is not empty,
        the function needs to terminate.

    """
    logger.info('Starting enqueue loop')
    subscriber = _get_subscriber(zmq_context)

    expected_address = 'master.broadcast.{0}'.format(
        config.get('job_runner_worker', 'api_key'))

    last_activity_dts = datetime.utcnow()
    reconnect_after_inactivity = config.getint(
        'job_runner_worker', 'reconnect_after_inactivity')

    while True:
        try:
            exit_queue.get(block=False)
            logger.info('Termintating enqueue loop')
            return
        except Empty:
            pass

        try:
            address, content = subscriber.recv_multipart(zmq.NOBLOCK)
            last_activity_dts = datetime.utcnow()
        except zmq.ZMQError:
            # this is needed in case the ZMQ publisher is load-balanced and the
            # loadbalancer dropped the connection to the backend, but not the
            # connection to our side. without this work-around, zmq will think
            # that all is well, and we won't receive anything anymore
            delta = datetime.utcnow() - last_activity_dts
            if delta > timedelta(seconds=reconnect_after_inactivity):
                logger.warning(
                    'There was not activity for {0}, reconnecting'
                    ' to publisher'.format(delta)
                )
                subscriber.close()
                time.sleep(random.randint(1, 10))
                subscriber = _get_subscriber(zmq_context)
                last_activity_dts = datetime.utcnow()
                continue
            else:
                time.sleep(0.5)
                continue

        # since zmq is subscribed to everything that starts with the given
        # prefix, we have to do a double check to make sure this is an exact
        # match.
        if not address == expected_address:
            continue

        logger.debug('Received [{0}]: {1}'.format(address, content))
        message = json.loads(content)

        if message['action'] == 'enqueue':
            _handle_enqueue_action(message, run_queue, event_queue)

        elif message['action'] == 'kill':
            _handle_kill_action(message, kill_queue, event_queue)

        elif message['action'] == 'ping':
            _handle_ping_action(message)

    subscriber.close()


def _get_subscriber(zmq_context):
    """
    Return a new subscriber connection for the given ``zmq_context``.
    """
    subscriber = zmq_context.socket(zmq.SUB)
    subscriber.connect('tcp://{0}:{1}'.format(
        config.get('job_runner_worker', 'broadcaster_server_hostname'),
        config.get('job_runner_worker', 'broadcaster_server_port'),
    ))
    subscriber.setsockopt(zmq.SUBSCRIBE, 'master.broadcast.{0}'.format(
        config.get('job_runner_worker', 'api_key')))
    return subscriber


def _handle_enqueue_action(message, run_queue, event_queue):
    """
    Handle the ``'enqueue'`` action.
    """
    run = Run('{0}{1}/'.format(
        config.get('job_runner_worker', 'run_resource_uri'),
        message['run_id']
    ))

    worker_list = Worker.get_list(
        config.get('job_runner_worker', 'worker_resource_uri')
    )

    if run.enqueue_dts:
        logger.warning(
            'Was expecting that run: {0} was not in queue yet'.format(
                run.id))
    elif len(worker_list) != 1:
        logger.warning('API returned multiple workers, expected one')
    else:
        run.patch({
            'enqueue_dts': datetime.now(utc).isoformat(' '),
            # set the worker so we know which worker of the pool claimed the
            # run
            'worker': worker_list[0].resource_uri,
        })
        run_queue.put(run)
        event_queue.put(json.dumps(
            {'event': 'enqueued', 'run_id': run.id, 'kind': 'run'}))


def _handle_kill_action(message, kill_queue, event_queue):
    """
    Handle the ``'kill'`` action.
    """
    kill_request = KillRequest('{0}{1}/'.format(
        config.get('job_runner_worker', 'kill_request_resource_uri'),
        message['kill_request_id']
    ))

    if kill_request.enqueue_dts:
        logger.warning(
            'Was expecting that kill: {0} was not in queue yet'.format(
                message['kill_request_id']))
    else:
        kill_request.patch({
            'enqueue_dts': datetime.now(utc).isoformat(' ')
        })
        kill_queue.put(kill_request)
        event_queue.put(json.dumps({
            'event': 'enqueued',
            'kill_request_id': kill_request.id,
            'kind': 'kill_request'
        }))


def _handle_ping_action(message):
    """
    Handle the ``'ping'`` action.
    """
    worker_list = Worker.get_list(
        config.get('job_runner_worker', 'worker_resource_uri')
    )

    if len(worker_list) == 1:
        worker_list[0].patch({
            'ping_response_dts': datetime.now(utc).isoformat(' '),
            'worker_version': job_runner_worker.__version__,
            'concurrent_jobs': config.getint(
                'job_runner_worker', 'concurrent_jobs')
        })
    else:
        logger.warning('API returned multiple workers, expected one')
