import hashlib
import hmac

from requests.auth import AuthBase


class HmacAuth(AuthBase):
    """
    Custom authentication for HMAC.
    """
    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret

    def __call__(self, r):
        hmac_message = '{method}{full_path}{body}'.format(
            method=r.method.upper(),
            full_path=r.path_url,
            body=r.data or '',
        )
        hmac_key = hmac.new(self.secret, hmac_message, hashlib.sha1)

        r.headers['Authorization'] = 'ApiKey {0}:{1}'.format(
            self.api_key, hmac_key.hexdigest())

        return r
