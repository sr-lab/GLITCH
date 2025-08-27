import ctypes
import json

lib = ctypes.CDLL('./glitch/rego/go/library/librego.so')

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
