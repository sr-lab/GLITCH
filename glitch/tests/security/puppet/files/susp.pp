define apache::mod (
  $package = undef,
  $package_ensure = 'present',
  $lib = undef,
  $lib_path = $::apache::params::lib_path,
  $id = undef,
  $path = undef,
) {
  if ! defined(Class['apache']) {
    fail('You must include the apache base class before using any apache defined resources')
  }

  $mod = $name
  #include apache #This creates duplicate resources in rspec-puppet
  $mod_dir = $::apache::mod_dir

  # Determine if we have special lib
  $mod_libs = $::apache::params::mod_libs
  $mod_lib = $mod_libs[$mod] # 2.6 compatibility hack
  if $lib {
    $_lib = $lib
  } elsif $mod_lib {
    $_lib = $mod_lib
  } else {
    $_lib = "mod_${mod}.so"
  }
}