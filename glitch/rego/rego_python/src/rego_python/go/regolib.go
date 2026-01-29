package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"context"
	"encoding/json"
	"fmt"
	"unsafe"

	"github.com/open-policy-agent/opa/rego"
	"github.com/open-policy-agent/opa/storage/inmem"
)

//export RunRego
func RunRego(inputJSON *C.char, dataJSON *C.char, modulesJSON *C.char) *C.char {
	input := C.GoString(inputJSON)
	data := C.GoString(dataJSON)
	modules := C.GoString(modulesJSON)

	var inputVal interface{}
	var dataVal map[string]interface{}
	var moduleMap map[string]string

	if err := json.Unmarshal([]byte(input), &inputVal); err != nil {
		return C.CString(fmt.Sprintf(`{"error": "failed to parse input: %s"}`, err))
	}

	if err := json.Unmarshal([]byte(data), &dataVal); err != nil {
		return C.CString(fmt.Sprintf(`{"error": "failed to parse data: %s"}`, err))
	}

	if err := json.Unmarshal([]byte(modules), &moduleMap); err != nil {
        return C.CString(fmt.Sprintf(`{"error": "failed to parse modules: %s"}`, err))
    }
    store := inmem.NewFromObject(dataVal)

    regoArgs := []func(*rego.Rego){}
    regoArgs = append(regoArgs, rego.Query("data.glitch.Glitch_Analysis"))
    regoArgs = append(regoArgs, rego.Input(inputVal))
    regoArgs = append(regoArgs, rego.Store(store))
	regoArgs = append(regoArgs, rego.Strict(true))

    for name, code := range moduleMap {
        regoArgs = append(regoArgs, rego.Module(name, code))
    }

    r := rego.New(regoArgs...)

	ctx := context.Background()
	results, err := r.Eval(ctx)

	if err != nil {
		return C.CString(fmt.Sprintf(`{"error": "rego evaluation failed: %s"}`, err))
	}

	if len(results) == 0 {
		return C.CString(`{"error":"query returned undefined"}`)
	}

	out, err := json.Marshal(results)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error": "output serialization failed: %s"}`, err))
	}

	return C.CString(string(out))
}

//export FreeCString
func FreeCString(str *C.char) {
    C.free(unsafe.Pointer(str))
}

func main() {}
