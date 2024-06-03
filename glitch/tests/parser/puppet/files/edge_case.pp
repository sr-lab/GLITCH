define ssh::client_config (
  $connections,
  $owner = $title,
  ) {

  $_user_home = getvar( "home_${owner}" )
  validate_absolute_path( $_user_home )

  if ( ! defined( File["${_user_home}/.ssh"] ) ) {
    file { "${_user_home}/.ssh":
      ensure => directory,
      owner  => $_config_owner,
      mode   => '0700',
    }
  }

  create_resources( ssh::private_key, $connections, {
    home  => $_user_home,
    owner => $owner,
  })

  file { "${_user_home}/.ssh/config":
    owner   => $owner,
    mode    => '0600',
    content => template( 'ssh/ssh_config.erb' )
  }

}
