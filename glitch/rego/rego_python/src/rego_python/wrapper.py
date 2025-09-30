import ctypes
import json
import platform
import os
from pathlib import Path

def _get_lib_path():
    system = platform.system().lower()      # 'windows', 'linux', 'darwin'
    machine = platform.machine().lower()    # 'x86_64', 'amd64', 'arm64', 'aarch64', etc.

    base = Path(__file__).parent / "bin"

    EXTENSIONS = {
        "linux": "so",
        "darwin": "dylib",
        "windows": "dll",
    }

    # normalize architecture names
    ARCH_MAP = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }

    try:
        arch = ARCH_MAP[machine]
        ext = EXTENSIONS[system]
    except KeyError:
        raise OSError(f"Unsupported platform: {system} {machine}")

    filename = f"librego-{system}-{arch}.{ext}"
    return base / filename


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
