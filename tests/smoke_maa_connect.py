#!/usr/bin/env python3
"""Load the official Linux MaaCore and connect through adb-cloud."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

ROOT = Path(os.getenv("MAA_ONLINE_ROOT", Path(__file__).resolve().parents[1]))
RUNTIME_HOME = Path(os.getenv("MAA_ONLINE_HOME", ROOT / "runtime/home"))
LIB_DIR = RUNTIME_HOME / ".local/share/maa/lib"
RESOURCE_DIR = RUNTIME_HOME / ".local/share/maa"
USER_DIR = RUNTIME_HOME / ".local/state/maa"
ADB = ROOT / "bin/adb-cloud"
USER_DIR.mkdir(parents=True, exist_ok=True)

os.environ["MAA_ONLINE_API"] = "http://127.0.0.1:22889"
os.environ["LD_LIBRARY_PATH"] = str(LIB_DIR) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")

lib = ctypes.CDLL(str(LIB_DIR / "libMaaCore.so"))
lib.AsstSetUserDir.argtypes = [ctypes.c_char_p]
lib.AsstSetUserDir.restype = ctypes.c_uint8
lib.AsstLoadResource.argtypes = [ctypes.c_char_p]
lib.AsstLoadResource.restype = ctypes.c_uint8
lib.AsstCreate.argtypes = []
lib.AsstCreate.restype = ctypes.c_void_p
lib.AsstSetInstanceOption.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_char_p]
lib.AsstSetInstanceOption.restype = ctypes.c_uint8
lib.AsstConnect.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
lib.AsstConnect.restype = ctypes.c_uint8
lib.AsstConnected.argtypes = [ctypes.c_void_p]
lib.AsstConnected.restype = ctypes.c_uint8
lib.AsstDestroy.argtypes = [ctypes.c_void_p]

assert lib.AsstSetUserDir(os.fsencode(USER_DIR)), "AsstSetUserDir failed"
assert lib.AsstLoadResource(os.fsencode(RESOURCE_DIR)), "AsstLoadResource failed"
handle = lib.AsstCreate()
assert handle, "AsstCreate failed"
try:
    # AsstInstanceOptionKey::TouchMode = 2, value 'adb'.
    assert lib.AsstSetInstanceOption(handle, 2, b"adb"), "setting ADB touch mode failed"
    connected = lib.AsstConnect(
        handle,
        os.fsencode(ADB),
        b"cloud-game:22888",
        b"General",
    )
    assert connected, "MaaCore failed to connect through adb-cloud"
    assert lib.AsstConnected(handle), "MaaCore did not remain connected"
finally:
    lib.AsstDestroy(handle)

print("MaaCore -> adb-cloud -> fake backend: PASS")
