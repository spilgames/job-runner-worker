import subprocess
import unittest2 as unittest

from mock import Mock, call, patch

from job_runner_worker.worker import execute_run


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.worker`.
    """
    @patch('job_runner_worker.worker.subprocess', subprocess)
    @patch('job_runner_worker.worker.get_tz_aware_now')
    @patch('job_runner_worker.worker.config')
    def test_execute_run(self, config, get_tz_aware_now):
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

        dts = get_tz_aware_now.return_value.isoformat.return_value

        self.assertEqual([
            call({'start_dts': dts}),
            call({
                'return_dts': dts,
                'return_log': u'H\xe9llo World!\n'.encode('utf-8'),
                'return_success': True,
            })
        ], run.patch.call_args_list)
        self.assertEqual([
            call('{"event": "started", "run_id": 1234}'),
            call('{"event": "returned", "run_id": 1234}'),
        ], event_queue.put.call_args_list)
