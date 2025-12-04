remote_file "#{cache_dir}/civicrm-#{civicrm_version}-l10n.tar.gz" do
  action :create_if_missing
  source "https://download.civicrm.org/civicrm-#{civicrm_version}-l10n.tar.gz"
  owner "wordpress"
  group "wordpress"
  mode "644"
  backup false
end