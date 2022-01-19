# -*- coding: utf-8 -*-
from os import urandom
from random import choice
from typing import List, Union
import base58
import uvarint
from bitarray import bitarray, frozenbitarray
from bitarray.util import ba2hex, ba2int, count_xor
from iscc_core.constants import IsccAny, UNITS, LN, MT, ST, ST_CC, ST_ID, ST_ISCC, VS, MC_PREFIX
from iscc_core.codec import (
    clean,
    decode_base32,
    decode_length,
    decode_units,
    encode_base32,
    encode_base64,
    encode_length,
    encode_units,
    read_header,
    write_header,
)


class Code:
    """
    Convenience class to handle different representations of an ISCC.
    """

    def __init__(self, code):
        # type: (IsccAny) -> None
        """
        Initialize a Code object from any kind of representation of an ISCC.

        :param AnyISCC code: Any valid representation of an ISCC
        """
        self._head = None
        self._body = None

        if isinstance(code, Code):
            code_fields = code._head + (code.hash_bytes,)
        elif isinstance(code, str):
            code = clean(code)
            code_fields = read_header(decode_base32(code))
        elif isinstance(code, tuple):
            code_fields = code
        elif isinstance(code, bytes):
            code_fields = read_header(code)
        else:
            raise ValueError(f"Code must be str, bytes, tuple or Code not {type(code)}")

        self._head = code_fields[:-1]
        body = bitarray()
        body.frombytes(code_fields[-1])
        self._body = frozenbitarray(body)

    def __str__(self):
        return self.code

    def __repr__(self):
        return f'Code("{self.code}")'

    def __bytes__(self):
        return self.bytes

    def __iter__(self):
        for f in self._head:
            yield f
        yield self.hash_bytes

    @property
    def code(self) -> str:
        """Standard base32 representation of an ISCC code."""
        return encode_base32(self.bytes)

    @property
    def uri(self) -> str:
        """Standard uri representation of an ISCC code."""
        return f"iscc:{self.code.lower()}"

    @property
    def bytes(self) -> bytes:
        """Raw bytes of code (including header)."""
        return self.header_bytes + self._body.tobytes()

    @property
    def hex(self) -> str:
        """Hex representation of code (including header)."""
        return self.bytes.hex()

    @property
    def uint(self) -> int:
        """Integer representation of code (including header)"""
        return int.from_bytes(self.bytes, "big", signed=False)

    @property
    def type_id(self) -> str:
        """A unique composite type-id (use as name to index codes seperately)."""
        if self.maintype == MT.ISCC:
            mtypes = decode_units(self._head[3])
            length = "".join([t.name[0] for t in mtypes]) + "DI"
        else:
            length = self.length
        return f"{self.maintype.name}-" f"{self.subtype.name}-" f"{self.version.name}-" f"{length}"

    @property
    def explain(self) -> str:
        """Human readble representation of code header."""
        if self.maintype == MT.ID:
            counter_bytes = self.hash_bytes[8:]
            if counter_bytes:
                counter = uvarint.decode(counter_bytes)
                return f"{self.type_id}-{self.hash_bytes[:8].hex()}-{counter.integer}"
        return f"{self.type_id}-{self.hash_hex}"

    @property
    def hash_bytes(self) -> bytes:
        """Byte representation of code (without header)"""
        return self._body.tobytes()

    @property
    def hash_hex(self) -> str:
        """Hex string representation of code (without header)."""
        return ba2hex(self._body)

    @property
    def hash_bits(self) -> str:
        """String of 0,1 representing the bits of the code (without header)."""
        return self._body.to01()

    @property
    def hash_ints(self) -> List[int]:
        """List of 0,1 integers representing the bits of the code (without header)."""
        return self._body.tolist(True)

    @property
    def hash_uint(self) -> int:
        """Unsinged integer representation of the code (without header)."""
        return ba2int(self._body, signed=False)

    @property
    def hash_ba(self) -> frozenbitarray:
        """Bitarray object of the code (without header)."""
        return self._body

    @property
    def header_bytes(self) -> bytes:
        """Byte representation of header prefix of the code"""
        return write_header(*self._head)

    @property
    def maintype(self) -> MT:
        """Enum maintype of code."""
        return MT(self._head[0])

    @property
    def subtype(self) -> Union[ST, ST_CC, ST_ISCC, ST_ID]:
        """Enum subtype of code."""
        if self.maintype == MT.CONTENT:
            return ST_CC(self._head[1])
        elif self.maintype == MT.ISCC:
            return ST_ISCC(self._head[1])
        elif self.maintype == MT.ID:
            return ST_ID(self._head[1])
        return ST(self._head[1])

    @property
    def version(self) -> VS:
        """Enum version of code."""
        return VS(self._head[2])

    @property
    def length(self) -> int:
        """Length of code hash in number of bits (without header)."""
        return decode_length(self._head[0], self._head[3])

    @classmethod
    def rnd(cls, mt=None, st=None, bits=64, data=None):
        """Returns a syntactically correct random code."""

        # MainType
        mt = choice(list(MT)) if mt is None else mt

        # SubType
        if st is None:
            if mt == MT.CONTENT:
                st = choice(list(ST_CC))
            elif mt == MT.ISCC:
                units = choice(UNITS)
                st = choice(list(ST_ISCC))
                st = st if (MT.SEMANTIC in units or MT.CONTENT in units) else ST_ISCC.SUM
                bits = len(units) * 64 + 128
            elif mt == MT.ID:
                st = choice(list(ST_ID))
            else:
                st = choice(list(ST))

        # Version
        vs = VS.V0

        # Length
        ln_bits = bits or choice(list(LN)).value
        if mt == MT.ISCC:
            # TODO fix ramdom ISCC with custom SubType generation
            ln_code = encode_units(units)
        else:
            ln_code = encode_length(mt, bits)

        # Body
        data = urandom(ln_bits // 8) if data is None else data

        return cls((mt, st, vs, ln_code, data))

    @property
    def mc_bytes(self):
        """ISCC header + body with multicodec prefix."""
        return MC_PREFIX + self.bytes

    @property
    def mf_base16(self) -> str:
        """Multiformats base16 encoded."""
        return "f" + self.mc_bytes.hex()

    @property
    def mf_base32(self) -> str:
        """Multiformats base32 encoded."""
        return "b" + encode_base32(self.mc_bytes).lower()

    @property
    def mf_base58btc(self) -> str:
        """Multiformats base58btc encoded."""
        return "z" + base58.b58encode(self.mc_bytes).decode("ascii")

    @property
    def mf_base64url(self) -> str:
        """Multiformats base64url encoded."""
        return "u" + encode_base64(self.mc_bytes)

    # TODO: bech32m support
    # @property
    # def bech32m(self):
    #     """Encode as bech32m with hrp `iscc`"""
    #     data = [bech32.CHARSET.find(c) for c in self.code.lower()]
    #     return bech32.bech32_encode(
    #         "iscc", data, bech32.Encoding.BECH32M
    #     )

    def __xor__(self, other) -> int:
        """Use XOR operator for hamming distance calculation."""
        return count_xor(self._body, other._body)

    def __eq__(self, other):
        # type: (Code) -> bool
        return self.code == other.code

    def __hash__(self):
        return self.uint