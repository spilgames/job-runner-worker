import json
import logging
import requests
import time
import urlparse
from requests.exceptions import RequestException

from job_runner_worker.auth import HmacAuth
from job_runner_worker.config import config


logger = logging.getLogger(__name__)


def retry_on_error(func):
    """
    Decorator the retry on (temporary) error while executing func.
    """
    def inner_func(*args, **kwargs):
        for i in range(3):
            try:
                if i > 0:
                    logger.warning('Attempt {0} to call {1}'.format(
                        i + 1, func.__name__))
                return func(*args, **kwargs)
            except RestError as e:
                logger.exception(
                    'Exception raised while calling {0}'.format(
                        func.__name__))
                time.sleep(i + 1)
        raise e

    return inner_func


class RestError(Exception):
    """
    Exception raised when a RESTful is returning an error.
    """


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

    @retry_on_error
    def _get_json_data(self):
        """
        Return JSON data.

        :raises:
            :exc:`.RestError` when response code is not 200.

        """
        try:
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
                raise RestError(
                    'GET request returned {0} - {1}'.format(
                        response.status_code, response.content))

            return response.json
        except RequestException as e:
            raise RestError('Exception {0} raised with message {1}'.format(
                e.__class__.__name__, str(e)))

    @retry_on_error
    def patch(self, attributes={}):
        """
        PATCH resource with given keyword arguments.

        :raises:
            :exc:`.RestError` when response code is not 202.

        """
        try:
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
                raise RestError(
                    'PATCH request returned {0} - {1}'.format(
                        response.status_code, response.content))
        except RequestException as e:
            raise RestError('Exception {0} raised with message {1}'.format(
                e.__class__.__name__, str(e)))

    @classmethod
    @retry_on_error
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
        try:
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
        except RequestException as e:
            raise RestError('Exception {0} raised with message {1}'.format(
                e.__class__.__name__, str(e)))

        if response.status_code != 200:
            raise RestError(
                'GET request returned {0}'.format(response.status_code))

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


class Job(BaseRestModel):
    """
    Model class for job resources.
    """
