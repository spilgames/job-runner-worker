import unittest2 as unittest

from mock import Mock, patch

from job_runner_worker.enqueuer import enqueue_runs
from job_runner_worker.models import RestError


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.enqueuer`.
    """
    @patch('job_runner_worker.enqueuer.config')
    @patch('job_runner_worker.enqueuer.datetime')
    @patch('job_runner_worker.enqueuer.Run')
    @patch('job_runner_worker.enqueuer.time')
    def test_enqueue_runs(self, time, Run, datetime, config):
        """
        Test :func:`.enqueue_runs`.
        """
        # just to break the never-ending loop :)
        time.sleep.side_effect = Exception('Boom!')

        queue = Mock()
        queue.full.side_effect = [False, True]
        event_queue = Mock()

        run = Mock()
        run.id = 1234

        Run.get_list.return_value = [run]

        self.assertRaises(Exception, enqueue_runs, queue, event_queue)

        Run.get_list.assert_called_once_with(
            config.get.return_value,
            params={
                'limit': 1,
                'state': 'scheduled',
                'schedule_dts__lte': datetime.utcnow.return_value
                    .isoformat.return_value
            }
        )

        run.patch.assert_called_once_with({
            'enqueue_dts': datetime.utcnow.return_value.isoformat.return_value
        })
        queue.put.assert_called_once_with(run)
        event_queue.put.assert_called_once_with(
            '{"event": "enqueued", "run_id": 1234}')

    @patch('job_runner_worker.enqueuer.logger')
    @patch('job_runner_worker.enqueuer.config')
    @patch('job_runner_worker.enqueuer.datetime')
    @patch('job_runner_worker.enqueuer.Run')
    @patch('job_runner_worker.enqueuer.time')
    def test_enqueue_runs_exception(self, time, Run, datetime, config, logger):
        """
        Test :func:`.enqueue_runs` raising exception.
        """
        # just to break the never-ending loop :)
        time.sleep.side_effect = Exception('Boom!')

        queue = Mock()
        queue.full.side_effect = [False, True]
        event_queue = Mock()

        Run.get_list.side_effect = RestError('Bam!')

        self.assertRaises(Exception, enqueue_runs, queue, event_queue)
        self.assertEqual(1, logger.exception.call_count)
