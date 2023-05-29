file { '/etc/foo':
  ensure => file,
  target => '/etc/foo',
  mode   => '0777',
}