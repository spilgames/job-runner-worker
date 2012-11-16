import unittest2 as unittest

from mock import call, patch

from job_runner_worker.runner import run


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.runner`.
    """
    @patch('job_runner_worker.runner.sys')
    @patch('job_runner_worker.runner.zmq')
    @patch('job_runner_worker.runner.publish')
    @patch('job_runner_worker.runner.reset_incomplete_runs')
    @patch('job_runner_worker.runner.execute_run')
    @patch('job_runner_worker.runner.enqueue_runs')
    @patch('job_runner_worker.runner.gevent')
    @patch('job_runner_worker.runner.Queue')
    @patch('job_runner_worker.runner.config')
    def test_run(
            self,
            config,
            Queue,
            gevent,
            enqueue_runs,
            execute_run,
            reset_incomplete_runs,
            publish,
            zmq,
            sys):
        """
        Test :func:`.run`.
        """
        def config_side_effect(*args):
            return {
                ('job_runner_worker', 'concurrent_jobs'): 4,
            }[args]

        config.getint.side_effect = config_side_effect

        run()

        reset_incomplete_runs.assert_called_once_with()

        self.assertEqual([
            call(
                enqueue_runs,
                zmq.Context.return_value,
                Queue.return_value,
                Queue.return_value,
            ),
            call(execute_run, Queue.return_value, Queue.return_value),
            call(execute_run, Queue.return_value, Queue.return_value),
            call(execute_run, Queue.return_value, Queue.return_value),
            call(execute_run, Queue.return_value, Queue.return_value),
            call(
                publish,
                zmq.Context.return_value,
                Queue.return_value,
            )
        ], gevent.spawn.call_args_list)

        sys.exit.assert_called_once()
