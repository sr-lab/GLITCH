yum_repository 'datadog' do
    name 'datadog'
      description 'datadog'
    proxy node['datadog']['yumrepo_proxy']
    proxy_username node['datadog']['yumrepo_proxy_username']
    proxy_password node['datadog']['yumrepo_proxy_password']
    gpgkey node['datadog']['yumrepo_gpgkey']
    gpgcheck true
    action :create
end