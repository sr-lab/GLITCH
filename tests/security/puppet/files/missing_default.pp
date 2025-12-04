$php_prefix = $::osfamily ? {
    'debian' => 'php5-',
    'redhat' => 'php-',
}

case $facts['os']['name'] {
  'RedHat', 'CentOS':  { include role::redhat  }
  /^(Debian|Ubuntu)$/: { include role::debian  }
}
