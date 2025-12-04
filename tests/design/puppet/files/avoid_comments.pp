class contrail::collector::service(
    $contrail_logoutput = $::contrail::params::contrail_logoutput,
    $redis_service = $::contrail::params::redis_service
) {
    # Ensure the services needed are running.
    exec { 'redis-del-db-dir':
        command   => 'rm -f /var/lib/redis/dump.rb',
        provider  => shell,
        logoutput => $contrail_logoutput
    } ->
    service { [$redis_service, 'supervisor-analytics'] :
        ensure => running,
        enable => true,
    }
}