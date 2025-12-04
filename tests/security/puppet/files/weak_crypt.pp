class govuk_postgresql::env_sync_user (
  $password
) {
  @postgresql::server::role { 'env-sync':
    password_hash => postgresql_password('env-sync', $password),
    tag           => 'govuk_postgresql::server::not_slave',
  }

  postgresql::server::pg_hba_rule { 'local access as env-sync user':
    type        => 'local',
    database    => 'all',
    auth_method => 'md5',
    order       => '001', # necessary to ensure this is before the 'local all all ident' rule.
  }
}