# Create/fix permissions on supplemental directories
%w(cache lib run).each do |folder|
  directory "fix permissions for /var/#{folder}/jenkins" do
    path "/var/#{folder}/jenkins"
    owner node['jenkins']['master']['user']
    group node['jenkins']['master']['group']
    mode node['jenkins']['master']['mode']
    action :create
  end
end