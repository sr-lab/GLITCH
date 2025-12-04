define contrail::lib::setup_passthrough_white_list(
    $dev_name,
) {
    $physnet = $title
    exec { "config_pci_whitelist_${title}":
        command   => "openstack-config --set /etc/nova/nova.conf DEFAULT pci_passthrough_whitelist ${wl}",
        provider  => shell,
        logoutput => true
    }

    $nova_pci_passthrough_whitelist_params = {
        'pci_passthrough_whitelist' => { value => '{ "devname": $dev_name, "physical_network": $physnet}'}
    }
}