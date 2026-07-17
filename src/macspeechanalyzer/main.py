import ctypes
from pathlib import Path
import logging

log = logging.getLogger(__name__)

LOG_CB = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
LIVE_CB = ctypes.CFUNCTYPE(None, ctypes.c_char_p)

@LOG_CB
def _log_cb(level, msg):
    log.log(level or logging.INFO, msg.decode("utf-8", "replace") if msg else "")

@LIVE_CB
def _live_cb(msg):
    print(msg.decode("utf-8", "replace") if msg else "", end="", flush=True)

_lib = ctypes.CDLL(str(Path(__file__).parent / f"libmacspeechanalyzer_core.dylib"))

# int32 msa_transcribe(const char* url, const char* locale, char** outText)
_lib.msa_transcribe.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
_lib.msa_transcribe.restype = ctypes.c_int32

# void msa_free_string(char* ptr)
_lib.msa_free_string.argtypes = [ctypes.c_void_p]
_lib.msa_free_string.restype = None

# char* msa_last_error() — strdup'ed message, caller frees
_lib.msa_last_error.argtypes = []
_lib.msa_last_error.restype = ctypes.c_void_p

_lib.msa_set_log_callback.argtypes = [LOG_CB]
_lib.msa_set_log_callback.restype = None
_lib.msa_set_log_callback(_log_cb)

_lib.msa_set_live_callback.argtypes = [LIVE_CB]
_lib.msa_set_live_callback.restype = None
_lib.msa_set_live_callback(_live_cb)


class SpeechAnalyzerError(Exception):
    pass

def _take_string(ptr: ctypes.c_void_p) -> str:
    """Copy a Swift-allocated C string into a Python str, then free it."""
    try:
        return ctypes.string_at(ptr).decode("utf-8")
    finally:
        _lib.msa_free_string(ptr)

def _raise_last_error(status: int) -> None:
    ptr = _lib.msa_last_error()
    msg = _take_string(ctypes.c_void_p(ptr)) if ptr else f"native error (status {status})"
    raise SpeechAnalyzerError(msg)

def transcribe(url: str, locale: str | None = None) -> str:
    out = ctypes.c_void_p()
    status = _lib.msa_transcribe(
        url.encode("utf-8"),
        locale.encode("utf-8") if locale is not None else None,
        ctypes.byref(out),                       # &out  ->  char**
    )
    if status != 0:
        _raise_last_error(status)
    if not out.value:
        raise SpeechAnalyzerError("transcribe returned success but no text")
    return _take_string(out)
    # TODO: end with newline if streaming mode is selected and no custom callback is set