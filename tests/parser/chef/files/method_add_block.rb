ot = template ::File.join(node['icinga2']['objects_dir'], "#{resource_name}.conf") do
    source "object.#{resource_name}.conf.erb"
    cookbook 'icinga2'
    owner node['icinga2']['user']
    group node['icinga2']['group']
    mode 0o640
    variables(:object => new_resource.name,
            :path => new_resource.path,
            :severity => new_resource.severity)
    notifies platform?('windows') ? :restart : :reload, 'service[icinga2]'
end