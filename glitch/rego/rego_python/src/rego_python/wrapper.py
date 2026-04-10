import ctypes
import json
import platform
from pathlib import Path
from typing import Optional, Any

_rego_available: bool = False
_rego_error: Optional[str] = None
_lib: Any = None


def _get_lib_path():
    system = platform.system().lower()  # 'windows', 'linux', 'darwin'
    machine = platform.machine().lower()  # 'x86_64', 'amd64', 'arm64', 'aarch64', etc.

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


def _load_lib() -> Any:
    global _rego_available, _rego_error, _lib
    try:
        lib_path = _get_lib_path()
        if not lib_path.exists():
            _rego_error = f"Rego library not found at {lib_path}"
            return None
        _lib = ctypes.CDLL(str(lib_path))
        _lib.RunRego.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        _lib.RunRego.restype = ctypes.c_void_p
        _lib.FreeCString.argtypes = [ctypes.c_void_p]
        _lib.FreeCString.restype = None
        _rego_available = True
        return _lib
    except OSError as e:
        _rego_error = str(e)
        return None


_load_lib()


def is_rego_available() -> bool:
    return _rego_available


def get_rego_error() -> Optional[str]:
    return _rego_error


def run_rego(
    input_data: dict[str, str], data: dict[str, str], rego_modules: dict[str, str]
):
    if _lib is None:
        raise RuntimeError(f"Rego library is not available: {_rego_error}")

    input_str = json.dumps(input_data)
    data_str = json.dumps(data)
    rego_modules_str = json.dumps(rego_modules)

    result_ptr = _lib.RunRego(
        input_str.encode("utf-8"),
        data_str.encode("utf-8"),
        rego_modules_str.encode("utf-8"),
    )

    result_json = ctypes.string_at(result_ptr).decode("utf-8")
    _lib.FreeCString(result_ptr)

    return json.loads(result_json)
