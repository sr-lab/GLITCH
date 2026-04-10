file { "/etc/apt/preferences.d/${name}.pref":
    content => template('openstack/apt-pinning.pref.erb'),
    ensure  => "present",
}