import ctypes
from pathlib import Path
import logging
from typing import Callable
import os

log = logging.getLogger(__name__)

LOG_CB = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)
SEGMENT_CB = ctypes.CFUNCTYPE(None, ctypes.c_char_p)

@LOG_CB
def _log_cb(level, msg):
    # for now, hacky: newline and flush stdout before/after each log print, otherwise logs may be bolted straight to a segment
    print("", flush=True)
    log.log(level or logging.INFO, msg.decode("utf-8", "replace") if msg else "")

@SEGMENT_CB
def _live_cb(msg):
    print(msg.decode("utf-8", "replace") if msg else "", end="", flush=True)

_lib = ctypes.CDLL(str(Path(__file__).parent / f"libmacspeechanalyzer_core.dylib"))

# int32 msa_transcribe(const char* url, const char* locale, char** outText, bool* emitLiveFragments)
_lib.msa_transcribe.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_bool]
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

_lib.msa_set_live_callback.argtypes = [SEGMENT_CB]
_lib.msa_set_live_callback.restype = None

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

def transcribe(path: str | Path, locale: str | None = None, on_segment: Callable[[str], None] | None = None) -> str:
    """Transcribe an audio file on-device.

    Runs synchronously and returns the full transcript once the file has
    been fully analyzed. If ``on_segment`` is provided, it is also invoked
    once per finalized segment as transcription progresses, allowing the
    caller to observe or display partial results without waiting for the
    final return value.

    Args:
        path: Filesystem path to the audio file to transcribe. Any format
            readable by ``AVAudioFile`` is accepted (e.g. wav, m4a, mp3,
            caf, aiff).
        locale: BCP 47 / Apple locale identifier (e.g. ``"en_US"``,
            ``"de_DE"``, ``"ja_JP"``) selecting the transcription language.
            If ``None``, the system's current locale is used when supported,
            otherwise English. If the requested locale's model is not yet
            installed on the device, it will be downloaded on first use.
        on_segment: Optional callback invoked from a background thread once
            per finalized transcript segment, in order, with the segment
            text as its single argument. Segments are non-overlapping and
            never revised, so appending them reconstructs the full
            transcript. Pass ``print`` to echo segments to stdout as they
            arrive.

    Returns:
        The complete transcript as a single string.

    Raises:
        FileNotFoundError: If ``url`` does not point to a readable file.
        RuntimeError: If the host is running a macOS version older than
            26.0, or if the native transcription pipeline fails.
    """
    emit_live_segments = False
    if on_segment is print:
        _lib.msa_set_live_callback(_live_cb)
        emit_live_segments = True
    elif on_segment is not None:
        def _trampoline(raw: bytes | None) -> None:
                    if raw is not None:
                        on_segment(raw.decode("utf-8", "replace"))
        cb = SEGMENT_CB(_trampoline)
        _lib.msa_set_live_callback(cb)
        emit_live_segments = True

    path = os.fspath(path)

    out = ctypes.c_void_p()
    status = _lib.msa_transcribe(
        path.encode("utf-8"),
        locale.encode("utf-8") if locale is not None else None,
        ctypes.byref(out),                       # &out  ->  char**
        emit_live_segments
    )
    if status != 0:
        _raise_last_error(status)
    if not out.value:
        raise SpeechAnalyzerError("transcribe returned success but no text")
    return _take_string(out)
