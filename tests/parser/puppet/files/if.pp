$test = @("TEST"/L)
    test 123
| TEST

if $x == 'absent' {
    file {'/usr/sbin/policy-rc.d':
        ensure  => absent,
    }
} else {
    file {'/usr/sbin/policy-rc.d':
        ensure  => present,
    }
}
