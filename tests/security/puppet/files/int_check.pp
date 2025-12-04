archive { $kib_name:
  ensure   => present,
  url      => $url,
  target   => $extract_location,
  checksum => false,
}

file { "${app_root}/config.js":
  ensure  => present,
  content => template('performanceplatform/kibana.config.js.erb'),
  require => Archive[$kib_name],
}