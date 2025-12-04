resource "test" "test" {
  sum = 1.3 + 1.4
  sub = 1.3 - 1.4
  mul = 1.3 * 1.4
  div = 1.3 / 1.4
  mod = 1.3 % 1.4
  and = 1.3 && 1.4
  or = 1.3 || 1.4
  eq = 1.3 == 1.4
  ne = 1.3 != 1.4
  gt = 1.3 > 1.4
  lt = 1.3 < 1.4
  ge = 1.3 >= 1.4
  le = 1.3 <= 1.4
  not = !true
  minus = -1.3
}
