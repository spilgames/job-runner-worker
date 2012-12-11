import json
import logging
from datetime import datetime

import zmq.green as zmq
from pytz import utc

from job_runner_worker.config import config
from job_runner_worker.models import Run


logger = logging.getLogger(__name__)


def enqueue_actions(zmq_context, run_queue, event_queue):
    """
    Populate the ``run_queue``.

    :param zmq_context:
        An instance of ``zmq.Context``.

    :param run_queue:
        An instance of ``Queue`` for pushing the runs to.

    :param event_queue:
        An instance of ``Queue`` for pushing events to.

    """
    logger.info('Start enqueue loop')

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
            run = Run('{0}{1}/'.format(
                config.get('job_runner_worker', 'run_resource_uri'),
                message['run_id']
            ))
            if run.enqueue_dts:
                logger.warning(
                    'Was expecting that {0} was not scheduled yet'.format(
                        run.id))
            else:
                run.patch({
                    'enqueue_dts': datetime.now(utc).isoformat(' ')
                })
                run_queue.put(run)
                event_queue.put(json.dumps(
                    {'event': 'enqueued', 'run_id': run.id}))

    subscriber.close()
