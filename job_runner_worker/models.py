import json
import logging
import requests
import time
import urlparse
from requests.exceptions import RequestException

from job_runner_worker.auth import HmacAuth
from job_runner_worker.config import config


logger = logging.getLogger(__name__)


class RequestClientError(Exception):
    """
    Exception raised when a RESTful request is returning an unexpected status
    in the 2xx, 3xx or 4xx range.
    """


class RequestServerError(Exception):
    """
    Exception raised when a RESTful request is returning a 5xx error.
    """


def retry_on_requests_error(func):
    """
    Decorator the retry on (temporary) error while executing func.
    """
    def inner_func(*args, **kwargs):
        attempt = 0

        while True:
            attempt += 1
            try:
                if attempt > 1:
                    logger.warning('Attempt {0} to call {1}'.format(
                        attempt, func.__name__))
                return func(*args, **kwargs)
            except (RequestException, RequestServerError):
                logger.exception(
                    'Exception raised while calling {0} '
                    'with arguments {1} '.format(
                        func.__name__, kwargs))
                if attempt <= 10:
                    time.sleep(2)
                elif attempt <= 50:
                    time.sleep(5)
                else:
                    time.sleep(10)
            except RequestClientError:
                # RequestClientError should theoretically not be recoverable
                # but we'll try max 5 times anyways.

                if attempt >= 5:
                    raise

                logger.exception(
                    'Exception raised while calling {0} '
                    'with arguments {1} '.format(
                        func.__name__, kwargs))
                time.sleep(attempt * 10)

    return inner_func


class BaseRestModel(object):
    """
    Base model around RESTful resources.

    :param resource_url:
        The path of the resource.

    :param initial_data:
        A ``dict`` containing initial data. Optional.

    """
    def __init__(self, resource_path, initial_data=None):
        self._resource_path = resource_path
        self._data = initial_data

    def __getattr__(self, name):
        if not self._data:
            self._data = self._get_json_data()
        return self._data[name]

    @retry_on_requests_error
    def _get_json_data(self):
        """
        Return JSON data.

        :raises:
            :exc:`!RequestException` on ``requests`` error.

        :raises:
            :exc:`.RequestServerError` on 5xx response.

        :raises:
            :exc:`.RequestClientError` on errors caused client-side.

        """
        response = requests.get(
            urlparse.urljoin(
                config.get('job_runner_worker', 'api_base_url'),
                self._resource_path
            ),
            auth=HmacAuth(
                config.get('job_runner_worker', 'api_key'),
                config.get('job_runner_worker', 'secret')
            ),
            headers={'content-type': 'application/json'},
            verify=False,
        )

        if response.status_code != 200:
            if response.status_code >= 500 and response.status_code <= 599:
                raise RequestServerError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))
            else:
                raise RequestClientError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))

        return response.json

    def reload(self):
        """
        Reload the model.
        """
        self._data = self._get_json_data()

    @retry_on_requests_error
    def patch(self, attributes={}):
        """
        PATCH resource with given keyword arguments.

        :raises:
            :exc:`!RequestException` on ``requests`` error.

        :raises:
            :exc:`.RequestServerError` on 5xx response.

        :raises:
            :exc:`.RequestClientError` on errors caused client-side.

        """
        response = requests.patch(
            urlparse.urljoin(
                config.get('job_runner_worker', 'api_base_url'),
                self._resource_path
            ),
            auth=HmacAuth(
                config.get('job_runner_worker', 'api_key'),
                config.get('job_runner_worker', 'secret')
            ),
            headers={'content-type': 'application/json'},
            data=json.dumps(attributes),
            verify=False,
        )

        if response.status_code != 202:
            if response.status_code >= 500 and response.status_code <= 599:
                raise RequestServerError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))
            else:
                raise RequestClientError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))

    @retry_on_requests_error
    def post(self, attributes={}):
        """
        PATCH resource with given keyword arguments.

        :raises:
            :exc:`!RequestException` on ``requests`` error.

        :raises:
            :exc:`.RequestServerError` on 5xx response.

        :raises:
            :exc:`.RequestClientError` on errors caused client-side.

        """
        response = requests.post(
            urlparse.urljoin(
                config.get('job_runner_worker', 'api_base_url'),
                self._resource_path
            ),
            auth=HmacAuth(
                config.get('job_runner_worker', 'api_key'),
                config.get('job_runner_worker', 'secret')
            ),
            headers={'content-type': 'application/json'},
            data=json.dumps(attributes),
            verify=False,
        )

        if response.status_code != 201:
            if response.status_code >= 500 and response.status_code <= 599:
                raise RequestServerError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))
            else:
                raise RequestClientError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))

    @classmethod
    @retry_on_requests_error
    def get_list(cls, resource_path, params={}):
        """
        Return a list of models for ``resource_path``.

        :param resource_path:
            The path of the resource.

        :param params:
            A ``dict`` containing optional request params. Optional.

        :return:
            A ``list`` of class instances.

        :raises:
            :exc:`.RestError` when response code is not 200.

        """
        response = requests.get(
            urlparse.urljoin(
                config.get('job_runner_worker', 'api_base_url'),
                resource_path
            ),
            auth=HmacAuth(
                config.get('job_runner_worker', 'api_key'),
                config.get('job_runner_worker', 'secret')
            ),
            params=params,
            headers={'content-type': 'application/json'},
            verify=False,
        )

        if response.status_code != 200:
            if response.status_code >= 500 and response.status_code <= 599:
                raise RequestServerError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))
            else:
                raise RequestClientError('Server returned {0} - {1}'.format(
                    response.status_code, response.content))

        output = []

        for obj_dict in response.json['objects']:
            output.append(cls(obj_dict['resource_uri'], obj_dict))

        if 'next' in response.json['meta'] and response.json['meta']['next']:
            output.extend(cls.get_list(response.json['meta']['next']))

        return output


class Run(BaseRestModel):
    """
    Model class for run resources.
    """
    @property
    def job(self):
        return Job(self.__getattr__('job'))

    @property
    def run_log(self):
        uri = self.__getattr__('run_log')
        if uri:
            return RunLog(uri)
        return None


class RunLog(BaseRestModel):
    """
    Model class for run log-output resources.
    """


class Job(BaseRestModel):
    """
    Model class for job resources.
    """


class KillRequest(BaseRestModel):
    """
    Model class for kill-requests.
    """
    @property
    def run(self):
        return Run(self.__getattr__('run'))


class Worker(BaseRestModel):
    """
    Model class for worker resources.
    """
