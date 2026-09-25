"""A simulated UDS (ISO 14229-1) ECU.

The transport is intentionally in-memory: call :meth:`handle` with a raw
request and get the raw response back, so the protocol logic can be
exercised without CAN hardware. To talk to a real ECU, replace the
caller of ``handle()`` with an ISO-TP/CAN layer (e.g. python-can).
"""

# --- Service identifiers -------------------------------------------------
SID_SESSION_CONTROL = 0x10
SID_ECU_RESET       = 0x11
SID_CLEAR_DTC       = 0x14
SID_READ_DTC        = 0x19
SID_READ_DID        = 0x22
SID_TESTER_PRESENT  = 0x3E

# --- Negative response codes ---------------------------------------------
NRC_SERVICE_NOT_SUPPORTED   = 0x11
NRC_SUBFUNC_NOT_SUPPORTED   = 0x12
NRC_BAD_LENGTH              = 0x13
NRC_CONDITIONS_NOT_CORRECT  = 0x22
NRC_REQUEST_OUT_OF_RANGE    = 0x31
NRC_SUBFUNC_NOT_SUPPORTED_IN_SESSION = 0x7E

# --- Diagnostic sessions ---------------------------------------------------
SESSION_DEFAULT  = 0x01
SESSION_EXTENDED = 0x03


def _negative(sid, nrc):
    return bytes((0x7F, sid, nrc))


class SimulatedEcu:
    """Minimal UDS server with a couple of DTCs and demo DIDs."""

    def __init__(self):
        self.session = SESSION_DEFAULT
        # Data identifiers: DID -> raw bytes
        self.dids = {
            0xF190: b"1HGCM82633A004352",  # VIN (17 ASCII chars)
            0xF18C: b"ECU-DEMO-01",        # ECU serial number
        }
        # Stored DTCs: list of (3-byte DTC id, status byte)
        self.dtcs = [(0xC12345, 0x2F), (0xD23456, 0x09)]

    # -- entry point ------------------------------------------------------
    def handle(self, request):
        request = bytes(request)
        if len(request) < 1:
            return _negative(0x00, NRC_BAD_LENGTH)
        sid = request[0]
        handler = {
            SID_SESSION_CONTROL: self._session_control,
            SID_ECU_RESET: self._ecu_reset,
            SID_CLEAR_DTC: self._clear_dtc,
            SID_READ_DTC: self._read_dtc,
            SID_READ_DID: self._read_did,
            SID_TESTER_PRESENT: self._tester_present,
        }.get(sid)
        if handler is None:
            return _negative(sid, NRC_SERVICE_NOT_SUPPORTED)
        return handler(request)

    # -- services -----------------------------------------------------------
    def _session_control(self, req):
        if len(req) != 2:
            return _negative(req[0], NRC_BAD_LENGTH)
        if req[1] not in (SESSION_DEFAULT, SESSION_EXTENDED):
            return _negative(req[0], NRC_SUBFUNC_NOT_SUPPORTED)
        self.session = req[1]
        return bytes((SID_SESSION_CONTROL + 0x40, req[1]))

    def _ecu_reset(self, req):
        if len(req) != 2:
            return _negative(req[0], NRC_BAD_LENGTH)
        if req[1] != 0x01:  # hardReset
            return _negative(req[0], NRC_SUBFUNC_NOT_SUPPORTED)
        self.session = SESSION_DEFAULT
        return bytes((SID_ECU_RESET + 0x40, req[1]))

    def _tester_present(self, req):
        if len(req) != 2:
            return _negative(req[0], NRC_BAD_LENGTH)
        if req[1] != 0x00:
            return _negative(req[0], NRC_SUBFUNC_NOT_SUPPORTED)
        return bytes((SID_TESTER_PRESENT + 0x40, 0x00))

    def _read_did(self, req):
        if len(req) != 3:
            return _negative(req[0], NRC_BAD_LENGTH)
        did = (req[1] << 8) | req[2]
        if did not in self.dids:
            return _negative(req[0], NRC_REQUEST_OUT_OF_RANGE)
        return bytes((SID_READ_DID + 0x40, req[1], req[2])) + self.dids[did]

    def _read_dtc(self, req):
        if len(req) < 2:
            return _negative(req[0], NRC_BAD_LENGTH)
        sub = req[1]
        if sub == 0x01:  # reportNumberOfDTCByStatusMask
            if len(req) != 3:
                return _negative(req[0], NRC_BAD_LENGTH)
            mask = req[2]
            count = sum(1 for _, st in self.dtcs if st & mask)
            return bytes((SID_READ_DTC + 0x40, sub, 0xFF, 0x01,
                          (count >> 8) & 0xFF, count & 0xFF))
        if sub == 0x02:  # reportDTCByStatusMask
            if len(req) != 3:
                return _negative(req[0], NRC_BAD_LENGTH)
            mask = req[2]
            out = bytearray((SID_READ_DTC + 0x40, sub, 0xFF))
            for dtc_id, st in self.dtcs:
                if st & mask:
                    out += bytes(((dtc_id >> 16) & 0xFF,
                                  (dtc_id >> 8) & 0xFF,
                                  dtc_id & 0xFF, st))
            return bytes(out)
        return _negative(req[0], NRC_SUBFUNC_NOT_SUPPORTED)

    def _clear_dtc(self, req):
        if len(req) != 4:
            return _negative(req[0], NRC_BAD_LENGTH)
        if self.session != SESSION_EXTENDED:
            return _negative(req[0], NRC_SUBFUNC_NOT_SUPPORTED_IN_SESSION)
        group = (req[1] << 16) | (req[2] << 8) | req[3]
        if group == 0xFFFFFF:
            self.dtcs = []
        else:
            self.dtcs = [(i, s) for i, s in self.dtcs if i != group]
        return bytes((SID_CLEAR_DTC + 0x40,))
