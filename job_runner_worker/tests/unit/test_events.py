import unittest2 as unittest

from mock import call, patch

from job_runner_worker.events import publish


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.events`.
    """
    @patch('job_runner_worker.events.config')
    @patch('job_runner_worker.events.zmq')
    def test_publish(self, zmq, config):
        """
        Test :func:`.websocket`.
        """
        def config_side_effect(*args):
            return {
                ('job_runner_worker', 'ws_server_hostname'): 'localhost',
                ('job_runner_worker', 'ws_server_port'): 5555,
            }[args]

        config.get.side_effect = config_side_effect

        context = zmq.Context.return_value
        publisher = context.socket.return_value

        event_queue = [
            'foo',
            'bar',
        ]

        publish(event_queue)

        self.assertEqual([
            call(['worker.event', 'foo']),
            call(['worker.event', 'bar']),
        ], publisher.send_multipart.call_args_list)
