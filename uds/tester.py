"""UDS tester (client) that talks to an ECU object."""

from .ecu import (
    SID_SESSION_CONTROL,
    SID_ECU_RESET,
    SID_CLEAR_DTC,
    SID_READ_DTC,
    SID_READ_DID,
    SID_TESTER_PRESENT,
    SESSION_EXTENDED,
)


class UdsError(Exception):
    """Raised when the ECU answers with a negative response."""

    def __init__(self, sid, nrc):
        super().__init__(
            f"Negative response: service 0x{sid:02X}, NRC 0x{nrc:02X}")
        self.sid = sid
        self.nrc = nrc


class Tester:
    """Sends UDS requests to ``ecu`` (anything with a ``handle()`` method)."""

    def __init__(self, ecu):
        self.ecu = ecu

    def _exchange(self, request, sid):
        resp = bytes(self.ecu.handle(bytes(request)))
        if len(resp) >= 3 and resp[0] == 0x7F:
            raise UdsError(resp[1], resp[2])
        if not resp or resp[0] != sid + 0x40:
            raise UdsError(sid, 0x00)
        return resp[1:]

    def diagnostic_session(self, session=SESSION_EXTENDED):
        """Enter a diagnostic session; returns the granted session."""
        data = self._exchange(bytes((SID_SESSION_CONTROL, session)),
                              SID_SESSION_CONTROL)
        return data[0]

    def tester_present(self):
        self._exchange(bytes((SID_TESTER_PRESENT, 0x00)), SID_TESTER_PRESENT)

    def ecu_reset(self):
        data = self._exchange(bytes((SID_ECU_RESET, 0x01)), SID_ECU_RESET)
        return data[0]

    def read_did(self, did):
        """Read a data identifier; returns the raw payload bytes."""
        data = self._exchange(
            bytes((SID_READ_DID, (did >> 8) & 0xFF, did & 0xFF)), SID_READ_DID)
        return bytes(data[2:])

    def dtc_count(self, status_mask=0xFF):
        data = self._exchange(bytes((SID_READ_DTC, 0x01, status_mask)),
                              SID_READ_DTC)
        return (data[3] << 8) | data[4]

    def read_dtcs(self, status_mask=0xFF):
        """Returns a list of (dtc_id, status) tuples."""
        data = self._exchange(bytes((SID_READ_DTC, 0x02, status_mask)),
                              SID_READ_DTC)
        dtcs = []
        i = 2  # skip sub-function + statusAvailabilityMask
        while i + 4 <= len(data):
            dtc_id = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2]
            dtcs.append((dtc_id, data[i + 3]))
            i += 4
        return dtcs

    def clear_dtcs(self, group=0xFFFFFF):
        """Clear DTCs (0xFFFFFF = all). Needs extended session."""
        self._exchange(bytes((SID_CLEAR_DTC, (group >> 16) & 0xFF,
                              (group >> 8) & 0xFF, group & 0xFF)),
                       SID_CLEAR_DTC)
