class openstack::profile::firewall::post {
  firewall { '9100 - Accept all vm network traffic':
    proto  => 'all',
    state  => ['NEW'],
    action => 'accept',
    source => $::openstack::config::network_data,
  } ->
  firewall { '9999 - Reject remaining traffic':
    proto  => 'all',
    action => 'reject',
    reject => 'icmp-host-prohibited',
    source => '0.0.0.0/0',
  }
}