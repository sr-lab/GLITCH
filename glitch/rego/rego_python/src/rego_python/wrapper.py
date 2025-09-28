import ctypes
import json
import platform
import os
from pathlib import Path

def _get_lib_path():
    system = platform.system().lower()
    machine = platform.machine().lower()

    base = Path(__file__).parent / "libs"
    if system == "linux" and "x86_64" in machine:
        return base / "linux-x86_64" / "librego.so"
    #elif system == "darwin" and "x86_64" in machine:
    #    return base / "darwin-x86_64" / "librego.dylib"
    #elif system == "windows" and "amd64" in machine:
    #    return base / "windows-x86_64" / "librego.dll"
    else:
        raise OSError(f"Unsupported platform: {system} {machine}")

lib = ctypes.CDLL(str(_get_lib_path()))

lib.RunRego.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
lib.RunRego.restype = ctypes.c_char_p

def run_rego(input_data: dict[str, str], data: dict[str, str], rego_modules: dict[str, str]):
    input_str = json.dumps(input_data)
    data_str = json.dumps(data)
    rego_modules_str = json.dumps(rego_modules)

    result_ptr = lib.RunRego(
        input_str.encode('utf-8'),
        data_str.encode('utf-8'),
        rego_modules_str.encode('utf-8'),
    )
    
    result_json = ctypes.string_at(result_ptr).decode('utf-8')
    return json.loads(result_json)
