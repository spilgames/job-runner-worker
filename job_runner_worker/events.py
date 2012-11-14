import json
import logging

import zmq.green as zmq

from job_runner_worker.config import config


logger = logging.getLogger(__name__)


def publish(event_queue):
    """
    Publish enqueued events to the WebSocket server.

    :param event_queue:
        A ``Queue`` instance for events to broadcast.

    """
    context = zmq.Context(1)
    publisher = context.socket(zmq.PUB)
    publisher.connect('tcp://{0}:{1}'.format(
        config.get('job_runner_worker', 'ws_server_hostname'),
        config.get('job_runner_worker', 'ws_server_port'),
    ))

    for event in event_queue:
        logger.debug('Sending event: {0}'.format(event))
        publisher.send_multipart(['worker.event', event])

    publisher.close()
    context.term()
