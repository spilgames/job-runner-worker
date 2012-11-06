import unittest2 as unittest

from mock import Mock

from job_runner_worker.auth import HmacAuth


class HmacAuthTestCase(unittest.TestCase):
    """
    Tests for :class:`.HmacAuth`.
    """
    def test_hmac_calculation(self):
        """
        Test HMAC calculation.
        """
        auth = HmacAuth('public', 'key')

        r = Mock()
        r.method = 'patch'
        r.path_url = '/path/?foo=bar'
        r.data = 'data body'
        r.headers = {}

        self.assertEqual(
            'ApiKey public:2b989ffc81712758d070fb46055b55f18a245d15',
            auth(r).headers['Authorization']
        )
