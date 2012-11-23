import unittest2 as unittest
from datetime import datetime

from mock import patch

from job_runner_worker.timezone import get_tz_aware_now


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`job_runner_worker.timezone`.
    """
    @patch('job_runner_worker.timezone.config')
    def test_get_tz_aware_now(self, config):
        """
        Test :func:`.get_tz_aware_now`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'timezone'): 'Europe/Amsterdam',
            }[args]

        config.get.side_effect = config_get_side_effect

        dts = get_tz_aware_now()

        self.assertTrue(isinstance(dts, datetime))
        self.assertEqual('Europe/Amsterdam', dts.tzinfo.zone)
