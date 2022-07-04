class aptly (
  String $package_ensure            = 'present',
  Stdlib::Absolutepath $config_file = '/etc/aptly.conf',
  Hash $config                      = {},
  Optional[String] $config_contents = undef,
  Boolean $repo                     = true,
  String $user                      = 'root',
  Hash $aptly_repos                 = {},
  Hash $aptly_mirrors               = {},
) {
  if $repo {
    Apt::Source['aptly'] -> Class['apt::update'] -> Package['aptly']
  }

  package { 'aptly':
    ensure  => $package_ensure,
  }

  $config_file_contents = $config_contents ? {
    undef   => inline_template("<%= Hash[@config.sort].to_pson %>\n"),
    default => $config_contents,
  }

  file { $config_file:
    ensure  => file,
    content => $config_file_contents,
  }

  $aptly_cmd = "/usr/bin/aptly -config ${config_file}"

  create_resources('::aptly::mirror', $aptly_mirrors)
}