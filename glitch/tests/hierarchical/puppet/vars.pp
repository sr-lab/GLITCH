$my_hash = {
'key1' => {
    'test1' => '1',
    'test2' => '2',
    },
'key2' => 'value2',
'key3' => 'value3',
}

$my_hash['key4']['key5'] = 'value5'

$configdir         = "${boxen::config::configdir}/php"
$datadir           = "${boxen::config::datadir}/php"
$pluginsdir        = "${root}/plugins"
$cachedir          = "${php::config::datadir}/cache"
$extensioncachedir = "${php::config::datadir}/cache/extensions"
