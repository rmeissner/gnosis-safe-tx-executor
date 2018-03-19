import binascii
import json

import requests

from service import settings
from service.api.ethereum.utils import sha3, pubtoaddr, ecrecover_to_pub


def get_sender(message, signature):
    # noinspection PyBroadException
    try:
        return binascii.hexlify(
            pubtoaddr(
                ecrecover_to_pub(binascii.unhexlify(message), binascii.unhexlify(signature))
            )
        ).lower().decode()
    except Exception:
        return None
