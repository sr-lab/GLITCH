execute "set initial migration level" do
  action :nothing
  command "cd /opt/opscode/embedded/service/partybus && ./bin/partybus init"
  subscribes :run, "file[#{OmnibusHelper.bootstrap_sentinel_file}]", :delayed
end