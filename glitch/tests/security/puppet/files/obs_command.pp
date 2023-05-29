exec { 'Running pack':
  command => 'pack foo bar',
  path    => '/usr/bin:/usr/sbin:/bin',
}