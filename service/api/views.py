import json
import string

import requests
import rlp
import time
from pywallet.utils import HDPrivateKey, HDKey
from rest_framework.decorators import api_view
from rest_framework.response import Response
from two1.bitcoin.utils import bytes_to_str

from service import settings
from service.api.ethereum.transactions import Transaction
from service.api.ethereum.utils import parse_int_or_hex, int_to_hex, parse_as_bin, is_numeric
from service.api.google import check_subscription_token
from service.settings import FUNDING_ACCOUNT_PHRASE

master_key = HDPrivateKey.master_key_from_mnemonic(FUNDING_ACCOUNT_PHRASE)
root_key = HDKey.from_path(master_key, "m/44'/60'/0'/0/0")
sender = root_key[-1].public_key.address()
HTTP_SUBSCRIPTION_TOKEN = 'HTTP_SUBSCRIPTION_TOKEN'

def _request_headers():
    return {
        "Content-Type": "application/json; UTF-8",
    }


def rpc_call(method, params):
    data = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    }
    return requests.post(u'https://rinkeby.infura.io', data=json.dumps(data)).json()


def rpc_result(method, param):
    return rpc_call(method, param)["result"]


def estimate_tx(sender, address, value, data):
    data = {
        "from": sender,
        "to": address,
        "value": "0x0" if value == 0 else int_to_hex(value),
        "data": data
    }
    return parse_int_or_hex(rpc_result("eth_estimateGas", [data]))


def _build_save_execute_transactions(address, value):
    # TODO: build correct payload
    return "0xa9059cbb" + address[2:].zfill(64) + int_to_hex(value)[2:].zfill(64)


def _send_transaction(address, value=0, data="", gas=None):
    nonce = parse_int_or_hex(rpc_result("eth_getTransactionCount", [sender, "pending"]))
    if not gas:
        gas = estimate_tx(sender, address, value, data)
    tx = Transaction(nonce, 100000000, gas, address, value, parse_as_bin(data)).sign(
        bytes_to_str(bytes(root_key[-1])[-32:]))
    return rpc_result("eth_sendRawTransaction", ["0x" + bytes_to_str(rlp.encode(tx))])


@api_view(["POST"])
def execute_tx(request):
    target = request.data.get("target")
    if not target or len(target) != 42 or not target.startswith("0x") or not all(
                    c in string.hexdigits for c in target[2:]):
        return Response({"error": "invalid safe address (format: <40 hex chars>)"}, 400)

    data = request.data.get("data")
    if not data or not data.startswith("0x") or not all(c in string.hexdigits for c in data[2:]):
        return Response({"error": "invalid data (format: <hex chars>)"}, 400)

    token = request.META.get(HTTP_SUBSCRIPTION_TOKEN)
    if not token or len(token) == 0:
        return Response({"error": "missing subscription token"}, 400)

    purchase = check_subscription_token(settings.ANDROID_PRODUCT_ID, token)
    current_time = int(round(time.time() * 1000))
    expiry_time_str = purchase.get("expiryTimeMillis")
    print("Expiry time: " + expiry_time_str)
    if not expiry_time_str or int(expiry_time_str) < current_time:
        return Response({"error": "no active subscription"}, 401)

    return Response({"hash": _send_transaction(target, data=data)})
