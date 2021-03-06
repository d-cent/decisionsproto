# -*- coding: utf-8 -*-

import oauth2
import time
import requests
import ssl
import json
import logging
from config import Config
from urlparse import urljoin

logger = logging.getLogger('helsinki_log')

base_url = "https://hki.hackpad.com/api/1.0"

api_method = "https://hki.hackpad.com/api/1.0/pad/create"


list_updated = base_url + "/edited-since/0"
pad_all = base_url + "/pads/all"


# uses 0-legged OAuth signature validation
def gen_params():
    return {'oauth_version': "1.0",
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': int(time.time())}


class HackpadApi():

    def __init__(self):
        config = Config()
        self.api_key = config.get_hackpad_api_key()
        self.api_secret = config.get_hackpad_api_secret()

    def create_pad(self, text):
        consumer = oauth2.Consumer(key=self.api_key, secret=self.api_secret)
        params = gen_params()
        params['oauth_consumer_key'] = consumer.key
        req = oauth2.Request(method='POST', url=api_method, parameters=params)
        signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, consumer, None)
        response = requests.post(req.to_url(), headers={'Content-Type': 'text/html'}, data=text, verify=True)
        if response.status_code == 200:
            return json.loads(response.text)['padId']
        else:
            logger.debug("Response: " + response.text)
            raise Exception("Error creating pad")

    def get_pad(self, pad_id):
        consumer = oauth2.Consumer(key=self.api_key, secret=self.api_secret)
        params = gen_params()
        params['oauth_consumer_key'] = consumer.key
        req = oauth2.Request(method='GET', url=(base_url + "/pad/%s/revisions" % str(pad_id)), parameters=params)
        signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, consumer, None)
        response = requests.get(req.to_url(), verify=True)
        if response.status_code == 200:
            logger.debug("Pad exists: " + response.text)
            return response.text
        elif response.status_code == 404:
            logger.debug("Non-existant pad: " + str(response.status_code))
            # logger.debug(response.text)
            return None
        else:
            logger.debug("Unexpected status code: " + str(response.status_code))
            logger.debug(response.text)
            raise Exception("Error checking existance of pad")

    def pad_exists(self, pad_id):
        return self.get_pad(pad_id) is not None

    def hackpad_url(self, id):
        return urljoin('https://hki.hackpad.com/', id)


# response = create_pad("NEW PAD\n a new pad")
# pad_id = response['padId']
# print get_pad('hel-2015-003137')
# print pad_exists('hel-2015-003137')
# print get_pad(pad_id)
