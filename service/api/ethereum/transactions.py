# -*- coding: utf-8 -*-
import rlp
from rlp.sedes import big_endian_int, binary
from rlp.utils import str_to_bytes, ascii_chr, encode_hex

# in the yellow paper it is specified that s should be smaller than
# secpk1n (eq.205)
from gnosis_funding.api.ethereum import utils
from gnosis_funding.api.ethereum.utils import normalize_key, ecsign

secpk1n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
null_address = b'\xff' * 20


class Transaction(rlp.Serializable):

    """
    A transaction is stored as:
    [nonce, gasprice, startgas, to, value, data, v, r, s]

    nonce is the number of transactions already sent by that account, encoded
    in binary form (eg.  0 -> '', 7 -> '\x07', 1000 -> '\x03\xd8').

    (v,r,s) is the raw Electrum-style signature of the transaction without the
    signature made with the private key corresponding to the sending account,
    with 0 <= v <= 3. From an Electrum-style signature (65 bytes) it is
    possible to extract the public key, and thereby the address, directly.

    A valid transaction is one where:
    (i) the signature is well-formed (ie. 0 <= v <= 3, 0 <= r < P, 0 <= s < N,
        0 <= r < P - N if v >= 2), and
    (ii) the sending account has enough funds to pay the fee and the value.
    """

    fields = [
        ('nonce', big_endian_int),
        ('gasprice', big_endian_int),
        ('startgas', big_endian_int),
        ('to', utils.address),
        ('value', big_endian_int),
        ('data', binary),
        ('v', big_endian_int),
        ('r', big_endian_int),
        ('s', big_endian_int),
    ]

    _sender = None

    def __init__(self, nonce, gasprice, startgas,
                 to, value, data, v=0, r=0, s=0):
        self.data = None

        to = utils.normalize_address(to, allow_blank=True)

        super(
            Transaction,
            self).__init__(
            nonce,
            gasprice,
            startgas,
            to,
            value,
            data,
            v,
            r,
            s)

    @property
    def network_id(self):
        if self.r == 0 and self.s == 0:
            return self.v
        elif self.v in (27, 28):
            return None
        else:
            return ((self.v - 1) // 2) - 17

    def sign(self, key, network_id=None):
        """Sign this transaction with a private key.

        A potentially already existing signature would be overridden.
        """
        if network_id is None:
            rawhash = utils.sha3(rlp.encode(self, UnsignedTransaction))
        else:
            assert 1 <= network_id < 2**63 - 18
            rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
                                 :-3] + [network_id, b'', b''])
            rawhash = utils.sha3(rlpdata)

        key = normalize_key(key)

        self.v, self.r, self.s = ecsign(rawhash, key)
        if network_id is not None:
            self.v += 8 + network_id * 2

        self._sender = utils.privtoaddr(key)
        return self

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self))

    def to_dict(self):
        d = {}
        for name, _ in self.__class__.fields:
            d[name] = getattr(self, name)
            if name in ('to', 'data'):
                d[name] = '0x' + encode_hex(d[name])
        d['sender'] = '0x' + encode_hex(self._sender)
        d['hash'] = '0x' + encode_hex(self.hash)
        return d

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.hash == other.hash

    def __lt__(self, other):
        return isinstance(other, self.__class__) and self.hash < other.hash

    def __hash__(self):
        return utils.big_endian_to_int(self.hash)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Transaction(%s)>' % encode_hex(self.hash)[:4]

    def __structlog__(self):
        return encode_hex(self.hash)


UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])