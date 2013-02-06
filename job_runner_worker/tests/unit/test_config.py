import unittest2 as unittest

from mock import Mock, patch

from job_runner_worker.config import get_config_parser, setup_log_handler


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :py:mod:`job_runner_worker.config`.
    """
    @patch('job_runner_worker.config.ConfigParser')
    @patch('job_runner_worker.config.os')
    def test_get_config_parser(self, os, ConfigParser):
        """
        Test :py:func:`.get_config_parser`.
        """
        os.environ = {'SETTINGS_PATH': '/path/to/settings'}

        config_mock = Mock()
        ConfigParser.ConfigParser.return_value = config_mock

        config = get_config_parser()

        ConfigParser.ConfigParser.assert_called_once_with({
            'log_level': 'info',
            'max_log_bytes': str(800 * 1024),
            'worker_resource_uri': '/api/v1/worker/',
            'run_resource_uri': '/api/v1/run/',
            'run_log_resource_uri': '/api/v1/run_log/',
            'kill_request_resource_uri': '/api/v1/kill_request/',
            'concurrent_jobs': '4',
            'ws_server_port': '5555',
            'broadcaster_server_port': '5556',
            'reconnect_after_inactivity': str(60 * 5),
        })
        config_mock.read.assert_called_once_with('/path/to/settings')
        self.assertEqual(config_mock, config)

    @patch('job_runner_worker.config.logging')
    def test_setup_log_handler(self, logging):
        """
        Test :func:`.setup_log_handler`.
        """
        setup_log_handler('INFO')

        logging.basicConfig.assert_called_once_with(
            level=logging.INFO,
            format='%(levelname)s - %(asctime)s - %(name)s: %(message)s',
        )
