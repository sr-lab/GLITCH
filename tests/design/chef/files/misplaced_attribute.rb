template "/etc/rsyslog.d/remote.conf" do
    action :create
    source "rsyslog.d.remote.conf.erb"
    owner "root"
    group "root"
    mode "0644"
    cookbook 'logging_rsyslog'
    variables(
      :remote_server => remote_server
    )
end