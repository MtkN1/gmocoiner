import hashlib
import hmac
import re
import time
import urllib.parse

from requests.auth import AuthBase


class GMOCoinAuth(AuthBase):
    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret
        
    def __call__(self, r):
        timestamp = str(int(time.time() * 1000))

        o = urllib.parse.urlparse(r.path_url).path
        p = re.sub(r'\A/(public|private)', '', o)
        text = timestamp + r.method + p + (r.body or '')
        sign = hmac.new(self.secret.encode('ascii'), text.encode('ascii'), hashlib.sha256).hexdigest()
        
        headers = dict(r.headers)
        headers['API-KEY'] = self.api_key
        headers['API-TIMESTAMP'] = timestamp
        headers['API-SIGN'] = sign
        r.prepare_headers(headers)
        
        return r
