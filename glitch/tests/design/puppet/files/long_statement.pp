oneview_volume{'volume_5':
    ensure  => 'get_attachable_volumes',
    require => Oneview_volume['volume_4'],
    data    => {
      query_parameters  => {
        connections    => "[{'networkUri':'/rest/fc-networks/90bd0f63-3aab-49e2-a45f-a52500b46616','proxyName':'20:19:50:EB:1A:0F:0E:B6','initiatorName':'10:00:62:01:F8:70:00:0E'}]"
      }
    }
}