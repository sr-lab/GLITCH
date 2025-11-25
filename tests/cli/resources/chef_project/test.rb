{
  "/etc/delivery/#{new_resource.chef_user}.pem" => new_resource.chef_user_pem,
  '/etc/chef/validation.pem' => new_resource.validation_pem,
}.each do |file, src|
  chef_file file do
    sensitive new_resource.sensitive if new_resource.sensitive
    source src
    user 'root'
    group 'root'
    mode '0644'
  end
end