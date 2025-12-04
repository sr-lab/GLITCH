define apache::vhost (
  Integer $port,
  String[1] $servername = $title,
) {
  $vhost_dir = $apache::params::vhost_dir

  file { "${vhost_dir}/${servername}.conf":
    ensure  => file,
    owner   => 'www',
    group   => 'www',
    mode    => '0644',
    content => template('apache/vhost-default.conf.erb'),
    require => Package['httpd'],
    notify  => Service['httpd'],
  }
}
