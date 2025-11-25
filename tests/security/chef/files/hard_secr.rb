user 'osmdata' do
  supports :manage_home => true
  comment 'osm data'
  uid '1201'
  gid 'osmdata'
  shell '/bin/bash'
  home '/home/osmdata'
  password '$1$gkl9sSWg$U9aIhckrcXwr08PLbx7NG1'
  system false
  action :create
  not_if "getent passwd osmdata"
end