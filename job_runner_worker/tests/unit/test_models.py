import unittest2 as unittest

from mock import Mock, patch
from requests.exceptions import RequestException

from job_runner_worker.models import (
    BaseRestModel,
    KillRequest,
    RequestClientError,
    RequestServerError,
    Run,
    retry_on_requests_error
)


class ModuleTestCase(unittest.TestCase):
    """
    Tests for :mod:`~job_runner_worker.models`.
    """
    @patch('job_runner_worker.models.time')
    def test_retry_on_requests_error(self, time):
        """
        Test :func:`.retry_on_requests_error`.
        """
        exceptions = [RequestException, RequestServerError, Exception]

        def func():
            exc = exceptions.pop(0)
            raise exc('Boom!')

        self.assertRaises(Exception, retry_on_requests_error(func))
        self.assertEqual(2, time.sleep.call_count)


class BaseRestModelTestCase(unittest.TestCase):
    """
    Tests for :class:`.BaseRestModel`.
    """
    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test_patch(self, requests, config, HmacAuth):
        """
        Test :meth:`.BaseRestModel.patch`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.patch.return_value
        response.status_code = 202

        base_model = BaseRestModel('/path/to/resource')
        base_model.patch({'field_name': 'field_value', 'published': True})

        requests.patch.assert_called_once_with(
            'http://api/path/to/resource',
            auth=HmacAuth.return_value,
            headers={'content-type': 'application/json'},
            data='{"field_name": "field_value", "published": true}',
            verify=False,
        )

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test_post(self, requests, config, HmacAuth):
        """
        Test :meth:`.BaseRestModel.post`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.post.return_value
        response.status_code = 201

        base_model = BaseRestModel('/path/to/resource')
        base_model.post({'field_name': 'field_value', 'published': True})

        requests.post.assert_called_once_with(
            'http://api/path/to/resource',
            auth=HmacAuth.return_value,
            headers={'content-type': 'application/json'},
            data='{"field_name": "field_value", "published": true}',
            verify=False,
        )

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test_patch_not_202(self, requests, config, HmacAuth):
        """
        Test :meth:`.BaseRestModel.patch`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.patch.return_value
        response.status_code = 418

        base_model = BaseRestModel('/path/to/resource')
        self.assertRaises(RequestClientError, base_model.patch, {'foo': 'bar'})

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test_post_not_201(self, requests, config, HmacAuth):
        """
        Test :meth:`.BaseRestModel.patch`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.post.return_value
        response.status_code = 418

        base_model = BaseRestModel('/path/to/resource')
        self.assertRaises(RequestClientError, base_model.post, {'foo': 'bar'})

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test__get_json_data(self, requests, config, HmacAuth):
        """
        Tests :meth:`.BaseRestModel._get_json_data`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.get.return_value
        response.status_code = 200

        base_model = BaseRestModel('/path/to/resource')

        self.assertEqual(response.json, base_model._get_json_data())

        requests.get.assert_called_once_with(
            'http://api/path/to/resource',
            auth=HmacAuth.return_value,
            headers={'content-type': 'application/json'},
            verify=False,
        )

        HmacAuth.assert_called_once_with('public', 'key')

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test__get_json_data_not_200(self, requests, config, HmacAuth):
        """
        Tests :meth:`.BaseRestModel._get_json_data` not returning 200.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.get.return_value
        response.status_code = 418

        base_model = BaseRestModel('/path/to/resource')

        self.assertRaises(RequestClientError, base_model._get_json_data)

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test_get_list(self, requests, config, HmacAuth):
        """
        Test :meth:`.BaseRestModel.get_list`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.get.return_value
        response.status_code = 200
        response.json = {
            'objects': [
                {'id': 1, 'resource_uri': 'foo'},
                {'id': 2, 'resource_uri': 'bar'},
            ],
            'meta': {
                'next': None,
            }
        }

        out = BaseRestModel.get_list('/path/to/resource')
        self.assertEqual(2, len(out))
        self.assertEqual({'id': 1, 'resource_uri': 'foo'}, out[0]._data)
        self.assertEqual({'id': 2, 'resource_uri': 'bar'}, out[1]._data)

    @patch('job_runner_worker.models.HmacAuth')
    @patch('job_runner_worker.models.config')
    @patch('job_runner_worker.models.requests')
    def test_get_list_not_200(self, requests, config, HmacAuth):
        """
        Test :meth:`.BaseRestModel.get_list`.
        """
        def config_get_side_effect(*args):
            return {
                ('job_runner_worker', 'api_base_url'): 'http://api/',
                ('job_runner_worker', 'secret'): 'key',
                ('job_runner_worker', 'api_key'): 'public',
            }[args]

        config.get.side_effect = config_get_side_effect
        response = requests.get.return_value
        response.status_code = 418

        self.assertRaises(
            RequestClientError, BaseRestModel.get_list, '/resource')

    def test___getattr__(self):
        """
        Test ``__getattr__``.
        """
        base_model = BaseRestModel(Mock())
        base_model._get_json_data = Mock(return_value={'foo': 'bar'})
        self.assertEqual('bar', base_model.foo)


class RunTestCase(unittest.TestCase):
    """
    Tests for :class:`.Run`.
    """
    @patch('job_runner_worker.models.Job')
    def test_job_property(self, JobMock):
        """
        Test job property.
        """
        run_model = Run(Mock(), {'job': '/job/resource'})

        self.assertEqual(JobMock.return_value, run_model.job)

        JobMock.assert_called_once_with('/job/resource')


class KillRequestTestCase(unittest.TestCase):
    """
    Tests for :class:`.KillRequest`.
    """
    @patch('job_runner_worker.models.Run')
    def test_run_property(self, RunMock):
        """
        Test run property.
        """
        kill_request_model = KillRequest(Mock(), {'run': '/run/resource'})

        self.assertEqual(RunMock.return_value, kill_request_model.run)
        RunMock.assert_called_once_with('/run/resource')
