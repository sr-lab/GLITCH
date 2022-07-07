 exec { 'storage_lm_boot_flag' :
  command   => "/bin/true  # comment to satisfy puppet syntax requirements
                set -x
                ifconfig livemnfsvgw
                RETVAL=\$?
                if [ \${RETVAL} -eq 0 ]
                then
                    openstack-config --set /etc/nova/nova.conf DEFAULT resume_guests_state_on_host_boot True
                fi
                #ensure we return success always
                exit 0
                ",
  logoutput => $contrail_logoutput,
}