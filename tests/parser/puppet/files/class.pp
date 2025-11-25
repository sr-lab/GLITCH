class apache (String $version = 'latest') {
  package { $httpd:
    ensure => $version,
    before => File['/etc/httpd.conf'],
  }
}
