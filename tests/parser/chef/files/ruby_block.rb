ruby_block "zabbix_ensure_super_admin_user_with_api_access" do
  block do
    username   = node.zabbix.api.username
    first_name = 'Zabbix'
  end
  notifies :restart
end

