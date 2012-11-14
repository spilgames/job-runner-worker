import subprocess
import unittest2 as unittest

from mock import Mock, call, patch

from job_runner_worker.worker import execute_run


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.worker`.
    """
    @patch('job_runner_worker.worker.subprocess', subprocess)
    @patch('job_runner_worker.worker.config')
    @patch('job_runner_worker.worker.datetime')
    def test_execute_run(self, datetime, config):
        """
        Test :func:`.execute_run`.
        """
        config.get.return_value = '/tmp'

        run = Mock()
        run.id = 1234
        run.job.script_content = (
            '#!/usr/bin/env bash\n\necho "Hello World!";\n')

        event_queue = Mock()

        execute_run([run], event_queue)

        dts = datetime.utcnow.return_value.isoformat.return_value

        self.assertEqual([
            call({'start_dts': dts}),
            call({
                'return_dts': dts,
                'return_log': 'Hello World!\n',
                'return_success': True,
            })
        ], run.patch.call_args_list)
        self.assertEqual([
            call('{"event": "started", "run_id": 1234}'),
            call('{"event": "returned", "run_id": 1234}'),
        ], event_queue.put.call_args_list)
