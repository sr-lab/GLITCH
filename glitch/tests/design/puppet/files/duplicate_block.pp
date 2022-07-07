node 'demo-server2.demo.juniper.net' {
    stage{ 'first': }
    stage{ 'last': }
    stage{ 'compute': }
    Stage['first']->Stage['main']->Stage['last']->Stage['compute']
    class { '::contrail::profile::common' : stage => 'first' }
    class { '::contrail::profile::compute' : stage => 'compute' }
}

node 'demo-server1.demo.juniper.net' {
    stage{ 'first': }
    stage{ 'last': }
    stage{ 'compute': }
    Stage['first']->Stage['main']->Stage['last']->Stage['compute']
    class { '::contrail::profile::common' : stage => 'first' }
    include ::contrail::profile::keepalived
    include ::contrail::profile::haproxy
    include ::contrail::profile::database
    include ::contrail::profile::webui
    include ::contrail::profile::openstack_controller
    include ::contrail::profile::config
    include ::contrail::profile::controller
    include ::contrail::profile::collector
    class { '::contrail::profile::provision' : stage => 'last' }
}