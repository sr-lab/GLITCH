class php::config {
  require boxen::config

  $root              = "${boxen::config::home}/phpenv"
  $logdir            = "${boxen::config::logdir}/php"
  $configdir         = "${boxen::config::configdir}/php"
  $datadir           = "${boxen::config::datadir}/php"
  $pluginsdir        = "${root}/plugins"
  $cachedir          = "${php::config::datadir}/cache"
  $extensioncachedir = "${php::config::datadir}/cache/extensions"
}