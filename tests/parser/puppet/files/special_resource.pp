class {'apache':
  version => '2.2.21',
}

class {
  'apache-2':
    version => '2.2.21',
  ;
  'apache-3':
    version => '2.2.22'
}

file {
  default:
    ensure => file,
    owner  => 'root',
    mode   => '0600',
  ;
  ['ssh_host_dsa_key']:
    # use all defaults
  ;
  ['ssh_config']:
    mode  => '0644',
    group => 'wheel',
  ;
}

package { ['armitage', 'metasploit']:
  ensure => 'installed',
}

Exec <| title == 'modprobe nf_conntrack_proto_sctp' |> { returns => [0,1] }

Exec {
  provider => 'shell',
  path => '/usr/bin:/bin:/sbin:/usr/sbin',
  logoutput => true,
}
