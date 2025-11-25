define mysql::server::instance ($root_password = '', $debian_sys_maint_password = '') {

  class { 'mysql::server':
    root_password             => $root_password,
    debian_sys_maint_password => $debian_sys_maint_password,
  }
}