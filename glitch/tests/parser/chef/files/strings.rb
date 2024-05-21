x = "test #{test} test"
y = "#@test"
z = <<~KEYGEN.gsub(/^ +/, '')
chmod 0600 #{my_home}/.ssh/id_dsa
chmod 0644 #{my_home}/.ssh/id_dsa.pub
KEYGEN
w = /.+ #{test} .+/
y = "first" \
        "second"
k = `echo #{test}`