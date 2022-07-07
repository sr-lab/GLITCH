class { 'profile::icinga2::agent':
  endpoints  => {
    'NodeName' => {},
    'satellite.example.org' => {
      'host' => '172.16.2.11',
    },
  },
  zones     => {
    'ZoneName' => {
      'endpoints' => ['NodeName'],
      'parent' => 'dmz',
    },
    'dmz' => {
      'endpoints' => ['satellite.example.org'],
    },
  },
}