[![CI](https://github.com/Rohitreddy23/uds-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/Rohitreddy23/uds-simulator/actions)

# UDS Diagnostics Simulator

A **UDS (ISO 14229-1)** simulator in pure Python: a virtual ECU plus a
tester client, so you can exercise diagnostic services with **no CAN
hardware**.

Implemented services:

| SID | Service | What's covered |
|---|---|---|
| `0x10` | DiagnosticSessionControl | default / extended sessions |
| `0x11` | ECUReset | hard reset (returns to default session) |
| `0x14` | ClearDiagnosticInformation | clear all or a DTC group (extended session only) |
| `0x19` | ReadDTCInformation | `0x01` count by status mask, `0x02` report by status mask |
| `0x22` | ReadDataByIdentifier | demo DIDs (VIN `0xF190`, ECU serial `0xF18C`) |
| `0x3E` | TesterPresent | keep-alive |

Negative responses (`0x7F … NRC`) are implemented for unsupported
services, bad lengths, out-of-range DIDs, and session violations.

## Run the demo

```bash
python demo.py
```

```
1. Enter extended diagnostic session
   granted session -> 0x3
2. Read VIN (DID 0xF190)
   VIN -> 1HGCM82633A004352
3. Read stored DTCs
   DTC 0xC12345, status 0x2F
   DTC 0xD23456, status 0x09
4. Clear DTCs
   remaining DTCs -> 0
5. Read unknown DID (expect negative response, NRC 0x31)
   Negative response: service 0x22, NRC 0x31
```

## Tests

```bash
python test_uds.py
```

## Notes

- The transport is in-memory on purpose: `Tester` calls
  `SimulatedEcu.handle()` directly. Swap that call with an ISO-TP/CAN
  layer (e.g. `python-can`) to talk to real hardware — the protocol
  logic stays the same.
- DTCs, DIDs and session rules are demo data, not a real ECU's.

Personal learning project — built to keep UDS service/NRC handling handy.
