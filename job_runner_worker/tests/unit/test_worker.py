import subprocess
import unittest2 as unittest

from gevent.queue import Queue, Empty
from mock import Mock, call, patch
from pytz import utc

from job_runner_worker.worker import (
    execute_run, kill_run, _get_child_pids, _truncate_log
)


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.worker`.
    """
    @patch('job_runner_worker.worker.subprocess', subprocess)
    @patch('job_runner_worker.worker.RunLog')
    @patch('job_runner_worker.worker.datetime')
    @patch('job_runner_worker.worker.config')
    def test_execute_run(self, config, datetime, RunLog):
        """
        Test :func:`.execute_run`.
        """
        config.get.return_value = '/tmp'

        run = Mock()
        run.id = 1234
        run.job.script_content = (
            u'#!/usr/bin/env bash\n\necho "H\xe9llo World!";\n')

        event_queue = Mock()
        exit_queue = Mock()
        run_queue = Queue()
        run_queue.put(run)

        exit_queue_return = [Empty, None]

        def exit_queue_side_effect(*args, **kwargs):
            value = exit_queue_return.pop(0)
            if callable(value):
                raise value()

        exit_queue.get.side_effect = exit_queue_side_effect

        execute_run(run_queue, event_queue, exit_queue)

        dts = datetime.now.return_value.isoformat.return_value
        self.assertTrue('pid' in run.patch.call_args_list[1][0][0])
        self.assertEqual(dts, run.patch.call_args_list[0][0][0]['start_dts'])
        self.assertEqual(
            u'H\xe9llo World!\n'.encode('utf-8'),
            RunLog.return_value.post.call_args_list[0][0][0]['content']
        )
        self.assertEqual([
            call({
                'return_dts': dts,
                'return_success': True,
            })
        ], run.patch.call_args_list[2:])
        self.assertEqual([
            call('{"kind": "run", "event": "started", "run_id": 1234}'),
            call('{"kind": "run", "event": "returned", "run_id": 1234}'),
        ], event_queue.put.call_args_list)
        datetime.now.assert_called_with(utc)

    @patch('job_runner_worker.worker.subprocess', subprocess)
    @patch('job_runner_worker.worker.RunLog')
    @patch('job_runner_worker.worker.datetime')
    @patch('job_runner_worker.worker.config')
    def test_execute_bad_shebang(self, config, datetime, RunLog):
        """
        Test :func:`.execute_run` when the shebang is invalid.
        """
        config.get.return_value = '/tmp'

        run = Mock()
        run.id = 1234
        run.job.script_content = (
            u'#!I love cheese\n\necho "H\xe9llo World!";\n')

        event_queue = Mock()
        exit_queue = Mock()
        run_queue = Queue()
        run_queue.put(run)

        exit_queue_return = [Empty, None]

        def exit_queue_side_effect(*args, **kwargs):
            value = exit_queue_return.pop(0)
            if callable(value):
                raise value()

        exit_queue.get.side_effect = exit_queue_side_effect

        execute_run(run_queue, event_queue, exit_queue)

        dts = datetime.now.return_value.isoformat.return_value

        self.assertEqual(dts, run.patch.call_args_list[0][0][0]['start_dts'])
        log_out = RunLog.return_value.post.call_args_list[0][0][0]['content']
        self.assertTrue(
            log_out.startswith('Could not execute job')
        )
        self.assertEqual([
            call({
                'return_dts': dts,
                'return_success': False,
            })
        ], run.patch.call_args_list[1:])
        self.assertEqual([
            call('{"kind": "run", "event": "started", "run_id": 1234}'),
            call('{"kind": "run", "event": "returned", "run_id": 1234}'),
        ], event_queue.put.call_args_list)
        datetime.now.assert_called_with(utc)

    @patch('job_runner_worker.worker._kill_pid_tree')
    @patch('job_runner_worker.worker.datetime')
    def test_kill_run(self, datetime, kill_pid_tree_mock):
        """
        Test :func:`.kill_run`.
        """
        event_queue = Mock()
        kill_request = Mock()
        kill_request.id = 1234
        kill_request.run.pid = 5678

        dts = datetime.now.return_value.isoformat.return_value

        kill_run([kill_request], event_queue)

        kill_pid_tree_mock.assert_called_with(5678)
        kill_request.patch.assert_called_with({
            'execute_dts': dts,
        })
        event_queue.put.assert_called_with((
            '{"kill_request_id": 1234, "kind": "kill_request", '
            '"event": "executed"}'
        ))

    @patch('job_runner_worker.worker.subprocess')
    def test__get_child_pids(self, subprocess_mock):
        """
        Test :func:`._get_child_pids`.
        """
        sub_proc = subprocess_mock.Popen.return_value
        sub_proc.wait.return_value = 0
        sub_proc.communicate.return_value = [' 123\n 456\n 789\n', '']

        self.assertEqual([123, 456, 789], _get_child_pids(321))

    @patch('job_runner_worker.worker.config')
    def test__truncate_log(self, config):
        """
        Test :func:`._truncate_log`.
        """
        config.getint.return_value = 100

        input_string = '{0}{1}'.format(
            ''.join(['a'] * 30), ''.join(['b'] * 100))
        expected_out = '{0}\n\n[truncated]\n\n{1}'.format(
            ''.join(['a'] * 20),
            ''.join(['b'] * 80),
        )

        self.assertEqual(expected_out, _truncate_log(input_string))
