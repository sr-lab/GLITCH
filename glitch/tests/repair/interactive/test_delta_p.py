from glitch.tests.repair.interactive.delta_p.delta_p_puppet_scripts import *


def test_delta_p_to_filesystems() -> None:
    statement = delta_p_puppet
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert len(fss[0].state) == 1
    assert "/var/www/customers/public_html/index.php" in fss[0].state
    assert (
        fss[0].state["/var/www/customers/public_html/index.php"].attrs["state"]
        == "present"
    )
    assert (
        fss[0].state["/var/www/customers/public_html/index.php"].attrs["mode"] == "0755"
    )
    assert (
        fss[0].state["/var/www/customers/public_html/index.php"].attrs["owner"]
        == "web_admin"
    )
    assert (
        fss[0].state["/var/www/customers/public_html/index.php"].attrs["content"]
        == "<html><body><h1>Hello World</h1></body></html>"
    )


def test_delta_p_to_filesystems_2() -> None:
    statement = delta_p_puppet_2
    fss = statement.to_filesystems()
    assert len(fss) == 1
    assert len(fss[0].state) == 1
    assert "/usr/sbin/policy-rc.d" in fss[0].state
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["state"] == "absent"
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["mode"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["owner"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["content"] == UNDEF


def test_delta_p_to_filesystems_if() -> None:
    statement = delta_p_puppet_if
    fss = statement.to_filesystems()
    assert len(fss) == 2
    assert len(fss[0].state) == 1
    assert "/usr/sbin/policy-rc.d" in fss[0].state
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["state"] == "absent"
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["mode"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["owner"] == UNDEF
    assert fss[0].state["/usr/sbin/policy-rc.d"].attrs["content"] == UNDEF

    assert len(fss[1].state) == 1
    assert "/usr/sbin/policy-rc.d" in fss[1].state
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["state"] == "present"
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["mode"] == UNDEF
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["owner"] == UNDEF
    assert fss[1].state["/usr/sbin/policy-rc.d"].attrs["content"] == UNDEF
