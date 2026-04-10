function apache::bool2http(Variant[String, Boolean] $arg) >> String {
  $rootgroup = $arg ? {
    'Redhat'                    => 'wheel',
    default                     => 'root',
  }
}
