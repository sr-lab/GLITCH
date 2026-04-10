Chef::Log.debug("Found chef-client in #{client_bin}")
node.default['chef_client']['bin'] = client_bin
create_directories

execute "install #{node['chef_client']['svc_name']} in SRC" do
  command "mkssys -s #{node['chef_client']['svc_name']} -p #{node['chef_client']['bin']} -u root -S -n 15 -f 9 -o #{node['chef_client']['log_dir']}/client.log -e #{node['chef_client']['log_dir']}/client.log -a '-i #{node['chef_client']['interval']} -s #{node['chef_client']['splay']}'"
  not_if "lssrc -s #{node['chef_client']['svc_name']}"
  action :run
end