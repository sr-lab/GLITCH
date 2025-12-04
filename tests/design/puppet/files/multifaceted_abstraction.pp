exec { 'clear_out_files' :
    command   => 'rm -f /etc/contrail/contrail*.out && rm -f /opt/contrail/contrail_packages/exec-contrail-setup-sh.out && echo reset_provision_3_0 >> /etc/contrail/contrail_common_exec.out',
    unless    => 'grep -qx reset_provision_3_0  /etc/contrail/contrail_common_exec.out',
    provider  => shell,
    logoutput => $contrail_logoutput
}