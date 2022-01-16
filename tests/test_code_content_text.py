# -*- coding: utf-8 -*-
import pytest
import iscc_core

TEXT_A = """
    Their most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_B = """
    The most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_C = """
    A need for open standard fingerprinting. We don´t need the best
    Fingerprinting algorithm just an accessible and widely used one.
"""


def test_hash_text_a():
    a = iscc_core.code_content_text.soft_hash_text_v0(TEXT_A).hex()
    assert a == "5f869a775c18bfbc3a117ab0114e13b2bf92614cda91513ee1f889fef3d6985f"


def test_hash_text_b():
    b = iscc_core.code_content_text.soft_hash_text_v0(TEXT_B).hex()
    assert b == "5f869a775c18bdfc3a117ab0114e13f2bf92610cda91513ee1f889bef3d6985f"


def test_hash_text_c():
    c = iscc_core.code_content_text.soft_hash_text_v0(TEXT_C).hex()
    assert c == "377b2f7b099a6df6bbc4a2ee4ff957b944c6434fa0e78842e7aad1169b71dd07"


def test_gen_text_code_a_default():
    a = iscc_core.code_content_text.gen_text_code_v0(TEXT_A)
    assert a.dict_raw() == {"iscc": "ISCC:EAARHV2U6PNK7WFX", "characters": 291}


def test_gen_text_code_a_32bits():
    a = iscc_core.code_content_text.gen_text_code_v0(TEXT_A, bits=32)
    assert a.dict_raw() == {"iscc": "ISCC:EAABHV2U6M", "characters": 291}


def test_code_text_b_128_bits():
    b = iscc_core.code_content_text.gen_text_code_v0(TEXT_B, 128)
    assert b.dict_raw() == {
        "iscc": "ISCC:EABRHV2U6PNKXWFXIEEYQLOQPICX6",
        "characters": 289,
    }


def test_code_text_c_256_bits():
    c = iscc_core.code_content_text.gen_text_code_v0(TEXT_C, 256)
    assert c.dict_raw() == {
        "iscc": "ISCC:EADWW36SS55HKIHAC3R3G2NDB3EGV7VCEA4CDPQH2NNRLSNJGPSDK4I",
        "characters": 129,
    }


def test_normalize_text():
    txt = "  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r"

    normalized = iscc_core.code_content_text.collapse_text(txt)
    assert normalized == "Internation alizætiøn☃💩 is a tric ky thing!"

    assert iscc_core.code_content_text.collapse_text(" ") == ""
    assert iscc_core.code_content_text.collapse_text("  Hello  World ? ") == "Hello World ?"
    assert iscc_core.code_content_text.collapse_text("Hello\nWorld") == "Hello World"


def test_code_text_empty():
    r64 = iscc_core.code_content_text.gen_text_code(b"", bits=64)
    assert r64.dict_raw() == {"iscc": "ISCC:EAASL4F2WZY7KBXB", "characters": 0}
    r128 = iscc_core.code_content_text.gen_text_code("", bits=128)
    assert r128.dict_raw() == {
        "iscc": "ISCC:EABSL4F2WZY7KBXBYUZPREWZ26IXU",
        "characters": 0,
    }


def test_code_text_non_utf8_raises():
    with pytest.raises(UnicodeDecodeError):
        iscc_core.code_content_text.gen_text_code(b"\x80", bits=64)
