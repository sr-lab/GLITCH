def method(param, *rest, **kwargs)
    x = 1
end

def object.method(param)
    x = 1
end

->(value) { value * 2 }
