case node[:platform_family]
when "rhel"
  default[:vmwaretools][:packages] = %w{ vmware-tools-core }
when "debian"
  default[:vmwaretools][:packages] = %w{ }
end