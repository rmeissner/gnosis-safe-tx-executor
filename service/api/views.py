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
from service.api.ethereum.authentication import get_sender
from service.api.ethereum.transactions import Transaction
from service.api.ethereum.utils import parse_int_or_hex, int_to_hex, parse_as_bin, is_numeric, sha3
from service.api.google import check_subscription_token, check_product_token
from service.api.models import Credits, Order
from service.settings import FUNDING_ACCOUNT_PHRASE, DEFAULT_GAS_PRICE, GAS_PER_CREDIT, PRODUCT_CREDITS, MAX_CREDITS

master_key = HDPrivateKey.master_key_from_mnemonic(FUNDING_ACCOUNT_PHRASE)
root_key = HDKey.from_path(master_key, "m/44'/60'/0'/0/0")
sender = root_key[-1].public_key.address()
HTTP_SUBSCRIPTION_TOKEN = 'HTTP_SUBSCRIPTION_TOKEN'
HTTP_AUTH_ACCOUNT = 'HTTP_AUTH_ACCOUNT'
HTTP_AUTH_SIGNATURE = 'HTTP_AUTH_SIGNATURE'


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


def get_or_none(model, *args, **kwargs):
    # noinspection PyBroadException
    try:
        return model.objects.get(*args, **kwargs)
    except Exception:
        return None


def _build_save_execute_transactions(address, value):
    # TODO: build correct payload
    return "0xa9059cbb" + address[2:].zfill(64) + int_to_hex(value)[2:].zfill(64)


def _get_nonce():
    return parse_int_or_hex(rpc_result("eth_getTransactionCount", [sender, "pending"]))


def _estimate_transaction(address, value=0, data=""):
    return estimate_tx(sender, address, value, data)


def _send_transaction(address, nonce, gas, value=0, data=""):
    tx = Transaction(nonce, DEFAULT_GAS_PRICE, gas, address, value, parse_as_bin(data)).sign(
        bytes_to_str(bytes(root_key[-1])[-32:]))
    return rpc_result("eth_sendRawTransaction", ["0x" + bytes_to_str(rlp.encode(tx))])


@api_view(["POST"])
def execute_tx_subscription(request):
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

    purchase = check_subscription_token(settings.ANDROID_SUBSCRIPTION_ID, token)
    current_time = int(round(time.time() * 1000))
    expiry_time_str = purchase.get("expiryTimeMillis")
    print("Expiry time: " + expiry_time_str)
    if not expiry_time_str or int(expiry_time_str) < current_time:
        return Response({"error": "no active subscription"}, 401)

    nonce = _get_nonce()
    estimate = _estimate_transaction(target, data=data)
    return Response({"hash": _send_transaction(target, nonce, estimate, data=data)})


@api_view(["POST"])
def execute_tx_credits(request):
    account = request.META.get(HTTP_AUTH_ACCOUNT)
    signature = request.META.get(HTTP_AUTH_SIGNATURE)

    if not account or len(account) != 42 or not signature or len(signature) == 0:
        return Response({"error": "missing authentication"}, 401)

    if account != get_sender(account, signature):
        return Response({"error": "invalid authentication"}, 401)

    target = request.data.get("target")
    if not target or len(target) != 42 or not target.startswith("0x") or not all(
            c in string.hexdigits for c in target[2:]):
        return Response({"error": "invalid safe address (format: <40 hex chars>)"}, 400)

    data = request.data.get("data")
    if not data or not data.startswith("0x") or not all(c in string.hexdigits for c in data[2:]):
        return Response({"error": "invalid data (format: <hex chars>)"}, 400)

    nonce = _get_nonce()
    estimate = _estimate_transaction(target, data=data)
    required_credits = int(estimate / GAS_PER_CREDIT)

    account_credits = get_or_none(Credits, account=account)
    if not account_credits or account_credits.amount < required_credits:
        return Response({"error": "not enough credits"}, 403)
    account_credits.amount -= required_credits
    account_credits.save()

    # noinspection PyBroadException
    try:
        return Response({"hash": _send_transaction(target, nonce, estimate, data=data)})
    except Exception:
        account_credits.amount += required_credits
        account_credits.save()
        return Response({"error": "could not commit transaction"})


@api_view(["POST"])
def estimate_tx_credits(request):
    account = request.META.get(HTTP_AUTH_ACCOUNT)
    signature = request.META.get(HTTP_AUTH_SIGNATURE)

    if not account or len(account) != 42 or not signature or len(signature) == 0:
        return Response({"error": "missing authentication"}, 401)

    if account != get_sender(sha3(account), signature):
        return Response({"error": "invalid authentication"}, 401)

    target = request.data.get("target")
    if not target or len(target) != 42 or not target.startswith("0x") or not all(
            c in string.hexdigits for c in target[2:]):
        return Response({"error": "invalid safe address (format: <40 hex chars>)"}, 400)

    data = request.data.get("data")
    if not data or not data.startswith("0x") or not all(c in string.hexdigits for c in data[2:]):
        return Response({"error": "invalid data (format: <hex chars>)"}, 400)

    estimate = _estimate_transaction(target, data=data)
    required_credits = int(estimate / GAS_PER_CREDIT)

    account_credits = get_or_none(Credits, account=account)
    return Response({
        "required_credits": required_credits,
        "balance": account_credits.amount if account_credits else 0
    })


@api_view(["POST"])
def redeem_voucher(request):
    account = request.META.get(HTTP_AUTH_ACCOUNT)
    signature = request.META.get(HTTP_AUTH_SIGNATURE)

    if not account or len(account) != 42 or not signature or len(signature) == 0:
        return Response({"error": "missing authentication"}, 401)

    recovered = get_sender(account, signature)
    print("expected %s, got %s" % (account, recovered))
    if account != recovered:
        return Response({"error": "invalid authentication"}, 401)

    token = request.data.get("voucher_id")
    if not token or len(token) == 0:
        return Response({"error": "missing voucher"}, 400)

    purchase = check_product_token(settings.ANDROID_PRODUCT_ID, token)
    if not purchase:
        return Response({"error": "invalid voucher"}, 400)

    order_id = purchase.get("orderId")
    consumption_state = purchase.get("consumptionState")
    purchase_state = purchase.get("purchaseState")

    if not order_id or consumption_state != 0 or purchase_state != 0:
        return Response({"error": "voucher has already be redeemed"}, 400)

    # noinspection PyBroadException
    try:
        Order.objects.create(account=account, id=order_id)
    except Exception:
        return Response({"error": "voucher has already be redeemed"}, 400)

    account_credits, _ = Credits.objects.get_or_create(account=account)
    if not account_credits or account_credits.amount + PRODUCT_CREDITS > MAX_CREDITS:
        return Response({"error": "maximum amounts of credits reached (%s)" % MAX_CREDITS}, 400)
    account_credits.amount += PRODUCT_CREDITS
    account_credits.save()

    return Response({"balance": account_credits.amount})


@api_view(["GET"])
def check_balance(request):
    account = request.META.get(HTTP_AUTH_ACCOUNT)
    signature = request.META.get(HTTP_AUTH_SIGNATURE)

    if not account or len(account) != 42 or not signature or len(signature) == 0:
        return Response({"error": "missing authentication"}, 401)

    if account != get_sender(account, signature):
        return Response({"error": "invalid authentication"}, 401)

    # noinspection PyBroadException
    try:
        account_credits = Credits.objects.create(account=account)
        return Response({"balance": account_credits.amount})
    except Exception:
        return Response({"balance": "0"})
