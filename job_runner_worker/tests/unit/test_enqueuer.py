import json
import unittest2 as unittest

from mock import Mock, patch
from pytz import utc

from job_runner_worker.enqueuer import enqueue_runs


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.enqueuer`.
    """
    @patch('job_runner_worker.enqueuer.datetime')
    @patch('job_runner_worker.enqueuer.config')
    @patch('job_runner_worker.enqueuer.Run')
    def test_enqueue_runs(self, Run, config, datetime):
        """
        Test :func:`.enqueue_runs`.
        """
        run_queue = Mock()
        event_queue = Mock()
        event_queue.put.side_effect = Exception('Boom!')

        zmq_context = Mock()
        subscriber = zmq_context.socket.return_value
        subscriber.recv_multipart.side_effect = lambda: ['foo', json.dumps({
            'run_id': 1234,
            'action': 'enqueue',
        })]

        run = Mock()
        run.id = 1234
        run.enqueue_dts = None

        Run.return_value = run

        self.assertRaises(
            Exception, enqueue_runs, zmq_context, run_queue, event_queue)

        run.patch.assert_called_once_with({
            'enqueue_dts': datetime.now.return_value.isoformat.return_value
        })
        run_queue.put.assert_called_once_with(run)
        event_queue.put.assert_called_once_with(
            '{"event": "enqueued", "run_id": 1234}')
        datetime.now.assert_called_with(utc)
