my_home = "/home/test"

execute "create ssh keypair for #{new_resource.username}" do
    user      new_resource.username
    command   <<-KEYGEN.gsub(/^ +/, '')
      ssh-keygen -t dsa -f #{my_home}/.ssh/id_dsa -N '' \
        -C '#{new_resource.username}@#{fqdn}-#{Time.now.strftime('%FT%T%z')}'
      chmod 0600 #{my_home}/.ssh/id_dsa
      chmod 0644 #{my_home}/.ssh/id_dsa.pub
    KEYGEN
    action    :nothing
end