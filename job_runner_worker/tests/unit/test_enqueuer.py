import unittest2 as unittest

import gevent
from gevent.queue import Queue
from mock import Mock, patch
from pytz import utc

from job_runner_worker.enqueuer import (
    _handle_enqueue_action,
    _handle_kill_action,
    _handle_ping_action,
    enqueue_actions
)


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.enqueuer`.
    """
    @patch('job_runner_worker.enqueuer._handle_enqueue_action')
    @patch('job_runner_worker.enqueuer.config')
    def test_enqueue_actions_enqueue(self, config, enqueue_action):
        """
        Test :func:`.enqueue_actions` with ``'enqueue'`` action.
        """
        config.get.return_value = 'foo'

        enqueue_action.side_effect = Exception('Boom!')

        zmq_context = Mock()
        subscriber = zmq_context.socket.return_value
        subscriber.recv_multipart.return_value = [
            'master.broadcast.foo',
            '{"action": "enqueue"}'
        ]

        run_queue = Mock()
        kill_queue = Mock()
        event_queue = Mock()

        self.assertRaises(
            Exception,
            enqueue_actions,
            zmq_context,
            run_queue,
            kill_queue,
            event_queue,
            Queue()
        )

        enqueue_action.assert_called_once_with(
            {'action': 'enqueue'}, run_queue, event_queue)

    @patch('job_runner_worker.enqueuer.config')
    def test_enqueue_actions_exit(self, config):
        """
        Test :func:`.enqueue_actions` returning.

        The infinite loop should return because we put something in the
        ``exit_queue``.

        """
        config.get.side_effect = lambda *args: '.'.join(args)
        exit_queue = Queue()
        exit_queue.put(Mock())

        greenlet = gevent.spawn(
            enqueue_actions, Mock(), Mock(), Mock(), Mock(), exit_queue)
        greenlet.join()

    @patch('job_runner_worker.enqueuer._handle_kill_action')
    @patch('job_runner_worker.enqueuer.config')
    def test_enqueue_actions_kill(self, config, kill_action):
        """
        Test :func:`.enqueue_actions` with ``'kill'`` action.
        """
        config.get.return_value = 'foo'

        kill_action.side_effect = Exception('Boom!')

        zmq_context = Mock()
        subscriber = zmq_context.socket.return_value
        subscriber.recv_multipart.return_value = [
            'master.broadcast.foo',
            '{"action": "kill"}'
        ]

        run_queue = Mock()
        kill_queue = Mock()
        event_queue = Mock()

        self.assertRaises(
            Exception,
            enqueue_actions,
            zmq_context,
            run_queue,
            kill_queue,
            event_queue,
            Queue()
        )

        kill_action.assert_called_once_with(
            {'action': 'kill'}, kill_queue, event_queue)

    @patch('job_runner_worker.enqueuer.config')
    @patch('job_runner_worker.enqueuer.datetime')
    @patch('job_runner_worker.enqueuer.Run')
    def test__handle_enqueue_action(self, Run, datetime, config):
        """
        Test :func:`._handle_enqueue_action`.
        """
        run_queue = Mock()
        event_queue = Mock()

        run = Mock()
        run.id = 1234
        run.enqueue_dts = None
        Run.return_value = run

        message = {
            'action': 'enqueue',
            'run_id': 1234,
        }

        _handle_enqueue_action(message, run_queue, event_queue)

        run.patch.assert_called_once_with({
            'enqueue_dts': datetime.now.return_value.isoformat.return_value
        })
        run_queue.put.assert_called_once_with(run)
        event_queue.put.assert_called_once_with(
            '{"kind": "run", "event": "enqueued", "run_id": 1234}')
        datetime.now.assert_called_with(utc)

    @patch('job_runner_worker.enqueuer.config')
    @patch('job_runner_worker.enqueuer.datetime')
    @patch('job_runner_worker.enqueuer.KillRequest')
    def test__handle_kill_action(self, KillRequest, datetime, config):
        """
        Test :func:`._handle_kill_action`.
        """
        config.get.return_value = 'foo'

        kill_queue = Mock()
        event_queue = Mock()

        kill_request = Mock()
        kill_request.id = 1234
        kill_request.enqueue_dts = None
        KillRequest.return_value = kill_request

        message = {
            'action': 'kill',
            'kill_request_id': 1234,
        }

        _handle_kill_action(message, kill_queue, event_queue)

        kill_request.patch.assert_called_with({
            'enqueue_dts': datetime.now.return_value.isoformat.return_value
        })
        event_queue.put.assert_called_once_with((
            '{"kill_request_id": 1234, "kind": "kill_request", '
            '"event": "enqueued"}'
        ))
        datetime.now.assert_called_once_with(utc)

    @patch('job_runner_worker.enqueuer.datetime')
    @patch('job_runner_worker.enqueuer.Worker')
    @patch('job_runner_worker.enqueuer.config')
    def test__handle_ping_action(self, config, Worker, datetime):
        """
        Test func:`._handle_ping_action`.
        """
        config.get.side_effect = lambda *args: '.'.join(args)

        worker = Mock()
        Worker.get_list.return_value = [worker]

        _handle_ping_action(Mock())

        Worker.get_list.assert_called_once_with(
            'job_runner_worker.worker_resource_uri'
        )

        dts = datetime.now.return_value.isoformat.return_value
        worker.patch.assert_called_once_with({
            'ping_response_dts': dts
        })
