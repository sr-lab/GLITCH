my_home = "/home/test"

execute "create ssh keypair for #{new_resource.username}" do
    user      new_resource.username
    command   "test"
    action    :nothing
end