"""Self-tests for the UDS simulator (no third-party dependencies)."""
from uds import SimulatedEcu, Tester, UdsError


def _tester():
    return Tester(SimulatedEcu())


def test_session_control():
    t = _tester()
    assert t.diagnostic_session(0x03) == 0x03
    assert t.diagnostic_session(0x01) == 0x01


def test_read_vin():
    t = _tester()
    assert t.read_did(0xF190) == b"1HGCM82633A004352"


def test_unknown_did_negative_response():
    t = _tester()
    try:
        t.read_did(0x1234)
    except UdsError as e:
        assert e.nrc == 0x31, hex(e.nrc)
    else:
        raise AssertionError("expected UdsError")


def test_dtc_read_and_clear():
    t = _tester()
    t.diagnostic_session(0x03)
    assert t.dtc_count() == 2
    assert len(t.read_dtcs()) == 2
    t.clear_dtcs()
    assert t.dtc_count() == 0
    assert t.read_dtcs() == []


def test_clear_dtc_needs_extended_session():
    t = _tester()  # default session
    try:
        t.clear_dtcs()
    except UdsError as e:
        assert e.nrc == 0x7E, hex(e.nrc)
    else:
        raise AssertionError("expected UdsError")


def test_unsupported_service():
    ecu = SimulatedEcu()
    resp = ecu.handle(bytes((0x99,)))
    assert resp == bytes((0x7F, 0x99, 0x11)), resp.hex()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print("All tests passed.")
