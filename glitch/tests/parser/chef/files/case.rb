case value
when 1
  "one"
else
  "number"
end

case value
in 2 | 3
  "two or three"
else
  "number"
end

x = case value
in { key: }
end
