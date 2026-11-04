from forgejury.determinism import volatile_reasons


def test_date_flagged():
    assert "date" in volatile_reasons("2026-01-01")


def test_windows_path_flagged():
    assert "temp_or_absolute_path" in volatile_reasons(r"C:\Users\x\AppData\Local\Temp\x")


def test_unix_tmp_path_flagged():
    assert "temp_or_absolute_path" in volatile_reasons("/tmp/forgejury-xyz/out.txt")


def test_hex_address_flagged():
    assert "hex_address" in volatile_reasons("<object at 0x7f8a1c0b2d30>")


def test_uuid_flagged():
    assert "uuid" in volatile_reasons("id=550e8400-e29b-41d4-a716-446655440000")


def test_stable_value_not_flagged():
    assert volatile_reasons("5") == []
    assert volatile_reasons("hello world") == []
