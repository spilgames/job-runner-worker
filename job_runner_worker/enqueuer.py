import json
import logging
from datetime import datetime

import zmq.green as zmq
from pytz import utc

from job_runner_worker.config import config
from job_runner_worker.models import KillRequest, Run


logger = logging.getLogger(__name__)


def enqueue_actions(zmq_context, run_queue, kill_queue, event_queue):
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

    """
    logger.info('Starting enqueue loop')

    subscriber = zmq_context.socket(zmq.SUB)
    subscriber.connect('tcp://{0}:{1}'.format(
        config.get('job_runner_worker', 'broadcaster_server_hostname'),
        config.get('job_runner_worker', 'broadcaster_server_port'),
    ))
    subscriber.setsockopt(zmq.SUBSCRIBE, 'master.broadcast.{0}'.format(
        config.get('job_runner_worker', 'api_key')))

    expected_address = 'master.broadcast.{0}'.format(
        config.get('job_runner_worker', 'api_key'))

    while True:
        address, content = subscriber.recv_multipart()

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

    subscriber.close()


def _handle_enqueue_action(message, run_queue, event_queue):
    """
    Handle the ``'enqueue'`` action.
    """
    run = Run('{0}{1}/'.format(
        config.get('job_runner_worker', 'run_resource_uri'),
        message['run_id']
    ))

    if run.enqueue_dts:
        logger.warning(
            'Was expecting that run: {0} was not in queue yet'.format(
                run.id))
    else:
        run.patch({
            'enqueue_dts': datetime.now(utc).isoformat(' ')
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
