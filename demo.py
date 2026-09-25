"""Demo: run a full UDS session against the simulated ECU."""
from uds import SimulatedEcu, Tester, UdsError


def main():
    ecu = SimulatedEcu()
    t = Tester(ecu)

    print("1. Enter extended diagnostic session")
    print("   granted session ->", hex(t.diagnostic_session(0x03)))

    print("2. Read VIN (DID 0xF190)")
    print("   VIN ->", t.read_did(0xF190).decode())

    print("3. Read stored DTCs")
    for dtc_id, status in t.read_dtcs():
        print(f"   DTC 0x{dtc_id:06X}, status 0x{status:02X}")

    print("4. Clear DTCs")
    t.clear_dtcs()
    print("   remaining DTCs ->", t.dtc_count())

    print("5. Read unknown DID (expect negative response, NRC 0x31)")
    try:
        t.read_did(0x1234)
    except UdsError as e:
        print("  ", e)


if __name__ == "__main__":
    main()
