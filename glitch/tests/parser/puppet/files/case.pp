case $facts['os']['name'] {
  'RedHat', 'CentOS':  {
    User <| title == 'luke' |>

    file { '/etc/ntp.conf':
      ensure  => file,
    }
  }
  default:             { File['/etc/ntp.conf'] ~> Service['ntpd'] }
}
