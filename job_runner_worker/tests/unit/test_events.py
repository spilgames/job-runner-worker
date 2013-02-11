import unittest2 as unittest

from gevent.queue import Empty, Queue
from mock import Mock, call, patch

from job_runner_worker.events import publish


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.events`.
    """
    @patch('job_runner_worker.events.config')
    def test_publish(self, config):
        """
        Test :func:`.websocket`.
        """
        def config_side_effect(*args):
            return {
                ('job_runner_worker', 'ws_server_hostname'): 'localhost',
                ('job_runner_worker', 'ws_server_port'): 5555,
            }[args]

        config.get.side_effect = config_side_effect

        context = Mock()
        publisher = context.socket.return_value

        event_queue = Queue()
        event_queue.put('foo')
        event_queue.put('bar')
        exit_queue = Mock()

        publish(context, event_queue, exit_queue)

        self.assertEqual([
            call(['worker.event', 'foo']),
            call(['worker.event', 'bar']),
        ], publisher.send_multipart.call_args_list)
