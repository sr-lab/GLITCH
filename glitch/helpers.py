def remove_unmatched_brackets(string):
    stack, aux = [], ""

    for c in string:
        if c in ["(", "[", "{"]: 
            stack.append(c)
        elif (len(stack) > 0 
                and (c, stack[-1]) in [(")", "("), ("]", "["), ("}", "{")]):
            stack.pop()
        elif c in [")", "]", "}"]: 
            continue
        aux += c

    i, res = 0, ""
    while (len(stack) > 0 and i < len(aux)):
        if aux[i] == stack[0]:
            stack.pop(0)
            continue
        res += aux[i]
        i += 1
    res += aux[i:]

    return res