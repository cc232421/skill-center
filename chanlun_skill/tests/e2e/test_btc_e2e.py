from cli.main import run


def test_btc_e2e():
    r = run("BTCUSDT", "CRYPTO", "4h", "20240101", "20250601")
    assert r.get("error") is None, "fetch failed"
    structs = r.get("structures", {})
    fractals = structs.get("fractals", [])
    bis = structs.get("bis", [])
    segs = structs.get("segs", [])
    assert len(fractals) > 0, "fractals should exist"
    assert len(bis) > 0, "bis should be built"
    assert len(segs) > 0, "segs should be built"
