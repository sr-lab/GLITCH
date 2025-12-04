apache_module 'php5' do
  case node['platform_family']
  when 'rhel', 'fedora', 'freebsd'
    conf true
    filename 'libphp5.so'
  end
end

