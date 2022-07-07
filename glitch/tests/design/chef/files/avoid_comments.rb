include_recipe "nginx"

directory '/var/run/pypi' do
  owner 'www-data'
end

# Install the pypi.python.org site
template "#{node['nginx']['dir']}/sites-available/pypi.conf" do
  source "nginx_pypi.conf.erb"

  owner "root"
  group "root"
  mode "644"

  variables ({
    :domains => [
        "pypi.python.org", "cheeseshop.python.org", "a.pypi.python.org",
        "b.pypi.python.org", "d.pypi.python.org", "g.pypi.python.org",
    ],
    :root_dir => "/data/www/pypi",
    :packages_dir => "/data/packages",
    :static_dir => "/data/pypi/static",
    :hsts_seconds => 31536000,
    :uwsgi_sock => "unix:/var/run/pypi/pypi.sock",
    :upload_size => "100M",
    :default_server => true,
  })

  notifies :reload, resources(:service => 'nginx')
end