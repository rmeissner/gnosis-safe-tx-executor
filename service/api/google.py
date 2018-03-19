import json

import requests
import time

from oauth2client.service_account import ServiceAccountCredentials

from service import settings


def _get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.

    :return: Access token.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(settings.GOOGLE_CREDENTIALS), settings.GOOGLE_SCOPE)
    access_token_info = credentials.get_access_token()
    return access_token_info.access_token


def _request_headers():
    return {
        "Content-Type": "application/json; UTF-8",
        "Authorization": "Bearer " + _get_access_token(),
    }


def check_subscription_token(subscription_id, token, timeout=None):
    url = settings.GOOGLE_SUBSCRIPTIONS_ENDPOINT % (settings.GOOGLE_ANDROID_PACKAGE, subscription_id, token)
    response = requests.get(url, headers=_request_headers(), timeout=timeout)
    if 'Retry-After' in response.headers and int(response.headers['Retry-After']) > 0:
        sleep_time = int(response.headers['Retry-After'])
        time.sleep(sleep_time)
        return check_subscription_token(subscription_id, token, timeout)
    return response.json()


def check_product_token(product_id, token, timeout=None):
    url = settings.GOOGLE_PRODUCTS_ENDPOINT % (settings.GOOGLE_ANDROID_PACKAGE, product_id, token)
    response = requests.get(url, headers=_request_headers(), timeout=timeout)
    if 'Retry-After' in response.headers and int(response.headers['Retry-After']) > 0:
        sleep_time = int(response.headers['Retry-After'])
        time.sleep(sleep_time)
        return check_product_token(product_id, token, timeout)
    return response.json()
