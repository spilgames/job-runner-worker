import hashlib
import hmac

from requests.auth import AuthBase


class HmacAuth(AuthBase):
    """
    Custom authentication for HMAC.
    """
    def __init__(self, public_key, private_key):
        self.public_key = public_key
        self.private_key = private_key

    def __call__(self, r):
        hmac_message = '{method}{full_path}{body}'.format(
            method=r.method.upper(),
            full_path=r.path_url,
            body=r.data or '',
        )
        hmac_key = hmac.new(self.private_key, hmac_message, hashlib.sha1)

        r.headers['Authorization'] = 'ApiKey {0}:{1}'.format(
            self.public_key, hmac_key.hexdigest())

        return r
