import logging
import time

import zmq.green as zmq
from gevent.queue import Empty

from job_runner_worker.config import config


logger = logging.getLogger(__name__)


def publish(zmq_context, event_queue, exit_queue):
    """
    Publish enqueued events to the WebSocket server.

    :param zmq_context:
        An instance of ``zmq.Context``.

    :param event_queue:
        A ``Queue`` instance for events to broadcast.

    :param exit_queue:
        An instance of ``Queue`` to consume from. If this queue is not empty,
        the function needs to terminate.

    """
    logger.info('Starting event publisher')

    publisher = zmq_context.socket(zmq.PUB)
    publisher.connect('tcp://{0}:{1}'.format(
        config.get('job_runner_worker', 'ws_server_hostname'),
        config.get('job_runner_worker', 'ws_server_port'),
    ))

    while True:
        try:
            exit_queue.get(block=False)
            logger.info('Terminating event publisher')
            return
        except Empty:
            pass

        try:
            event = event_queue.get(block=False)
        except Empty:
            time.sleep(0.5)
            continue

        logger.debug('Sending event: {0}'.format(event))
        publisher.send_multipart(['worker.event', event])

    publisher.close()
