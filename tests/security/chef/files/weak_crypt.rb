def wildfly_user(user = nil, pass = nil, realm = 'ManagementRealm')
  user ||= 'chef-wildfly-' + SecureRandom.urlsafe_base64(5)
  pass ||= SecureRandom.urlsafe_base64(40)
  passhash = Digest::MD5.hexdigest "#{user}:#{realm}:#{pass}"
  {
    user: user.to_s,
    pass: pass.to_s,
    passhash: passhash.to_s,
  }
end