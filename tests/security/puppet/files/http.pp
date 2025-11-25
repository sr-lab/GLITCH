class profile::monitoring::netdata::haproxy(
  $stats_url = "http://${::ipaddress_public1}:9000/;csv;norefresh"
  ) {

  file_line { 'netdata-haproxy':
    ensure  => present,
    path    => '/opt/netdata/netdata-configs/python.d/haproxy.conf',
    line    => 'via_url:',
    match   => '^via_url:',
    require => Class['netdata']
  } ->
  file_line { 'netdata-haproxy-url':
    ensure  => present,
    path    => '/opt/netdata/netdata-configs/python.d/haproxy.conf',
    line    => " url: '${stats_url}'",
    after   => '^via_url:',
    require => Class['netdata']
  }
}