import unittest2 as unittest

from mock import Mock, call, patch

from job_runner_worker.cleanup import reset_incomplete_runs


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.cleanup`.
    """
    @patch('job_runner_worker.cleanup.Run')
    @patch('job_runner_worker.cleanup.config')
    def test_reset_incomplete_runs(self, config, Run):
        """
        Test :func:`.reset_incomplete_runs`.
        """
        def config_side_effect(*args):
            return {
                ('job_runner_worker', 'run_resource_uri'): '/api/run/'
            }[args]

        config.get.side_effect = config_side_effect

        incomplete_run = Mock()

        Run.get_list.side_effect = [[incomplete_run], []]

        reset_incomplete_runs()

        self.assertEqual([
            call('/api/run/', params={'state': 'in_queue'}),
            call('/api/run/', params={'state': 'started'}),
        ], Run.get_list.call_args_list)

        incomplete_run.patch.assert_called_once_with({
            'enqueue_dts': None,
            'start_dts': None,
        })
