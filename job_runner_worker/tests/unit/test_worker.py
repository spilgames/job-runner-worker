import subprocess
import unittest2 as unittest

from mock import Mock, call, patch
from pytz import utc

from job_runner_worker.worker import execute_run, kill_run, _truncate_log


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.worker`.
    """
    @patch('job_runner_worker.worker.subprocess', subprocess)
    @patch('job_runner_worker.worker.datetime')
    @patch('job_runner_worker.worker.config')
    def test_execute_run(self, config, datetime):
        """
        Test :func:`.execute_run`.
        """
        config.get.return_value = '/tmp'

        run = Mock()
        run.id = 1234
        run.job.script_content = (
            u'#!/usr/bin/env bash\n\necho "H\xe9llo World!";\n')

        event_queue = Mock()

        execute_run([run], event_queue)

        dts = datetime.now.return_value.isoformat.return_value

        self.assertTrue('pid' in run.patch.call_args_list[0][0][0])
        self.assertEqual(dts, run.patch.call_args_list[0][0][0]['start_dts'])
        self.assertEqual([
            call({
                'return_dts': dts,
                'return_log': u'H\xe9llo World!\n'.encode('utf-8'),
                'return_success': True,
            })
        ], run.patch.call_args_list[1:])
        self.assertEqual([
            call('{"kind": "run", "event": "started", "run_id": 1234}'),
            call('{"kind": "run", "event": "returned", "run_id": 1234}'),
        ], event_queue.put.call_args_list)
        datetime.now.assert_called_with(utc)

    @patch('job_runner_worker.worker.datetime')
    @patch('job_runner_worker.worker.subprocess')
    def test_kill_run(self, subprocess_mock, datetime):
        """
        Test :func:`.kill_run`.
        """
        event_queue = Mock()
        kill_request = Mock()
        kill_request.id = 1234
        kill_request.run.pid = 5678

        dts = datetime.now.return_value.isoformat.return_value

        kill_run([kill_request], event_queue)

        subprocess_mock.Popen.assert_called_with(['kill', '5678'])
        kill_request.patch.assert_called_with({
            'execute_dts': dts,
        })
        event_queue.put.assert_called_with((
            '{"kill_request_id": 1234, "kind": "kill_request", '
            '"event": "executed"}'
        ))

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
