define :sys_network_vlan_bridge, :interface => 'eth0' do
    vlan_id = params[:name]
  
    if vlan_id
      interface = params[:interface]
      vlan_interface = "#{interface}.#{vlan_id}"
      bridge = "br#{vlan_id}"
      if vlan_id == "0"
        node.default['sys']['network']['interfaces'][bridge] = {
          "bridge_ports" => interface
        }
      else
        node.default['sys']['network']['interfaces'][vlan_interface] = {
          "vlan-raw-device" => interface,
          "up" => "ifup #{bridge}"
        }
        node.default['sys']['network']['interfaces'][bridge] = {
          "auto" => false,
          "bridge_ports" => vlan_interface
        }
      end

      unless interface == node['network']['default_interface']
        node.default['sys']['network']['interfaces'][interface] = { "inet" => "static" }
      end
    end
end