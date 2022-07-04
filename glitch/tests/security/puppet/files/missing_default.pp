$php_prefix = $::osfamily ? {
    'debian' => 'php5-',
    'redhat' => 'php-',
}