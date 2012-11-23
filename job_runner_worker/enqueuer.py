import logging
import json

import zmq.green as zmq

from job_runner_worker.config import config
from job_runner_worker.models import Run
from job_runner_worker.timezone import get_tz_aware_now


logger = logging.getLogger(__name__)


def enqueue_runs(zmq_context, run_queue, event_queue):
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

    while True:
        address, content = subscriber.recv_multipart()
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
                    'enqueue_dts': get_tz_aware_now().isoformat(' ')
                })
                run_queue.put(run)
                event_queue.put(json.dumps(
                    {'event': 'enqueued', 'run_id': run.id}))

    subscriber.close()
