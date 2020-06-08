from hostnet import RemoteLink, RemoteNode, RemoteHost, RemoteOVSSwitch
from mininet.net import Mininet


def test_remote_host():
    """
    Test the creation of the Remote Host and usage of command execution
    :return:
    """
    remote = "mininet_host"
    username = "ubuntu"
    remoteNode = RemoteNode("h1", remote, username)
    assert remoteNode.cmd('pwd') == "/home/ubuntu\r\n"
    assert remoteNode.cmd('pwd') == "/home/tymchenko/PycharmProjects/mininet_\r\n"


def test_link(capsys):
    """
    Test connectivity between local and remote host via link
    (Without link there is no connectivity)
    :param capsys: just capture the std(out/err)
    :return:
    """
    remote = "mininet_host"
    username = "ubuntu"
    net = Mininet(host=RemoteHost, link=RemoteLink)
    h1 = net.addHost('h1')
    h2 = net.addHost('h2', serverIp=remote, user=username)
    h3 = net.addHost('h3')
    net.addLink(h1, h2)
    net.start()
    with capsys.disabled():
        print("Test connectivity between h1 and h3 (not connected)")
        assert net.ping([h1, h3]) == 100
        print("Done\nTest connectivity between h1 and h2 (connected)")
        assert net.ping([h1, h2]) == 0
        print('Done')


def test_local_switch(capsys):
    """
    Test connectivity between local and remote host via switch
    :param capsys:  just capture the std(out/err)
    :return:
    """
    remote = "mininet_host"
    username = "ubuntu"
    net = Mininet(host=RemoteHost, link=RemoteLink, switch=RemoteOVSSwitch)
    h1 = net.addHost('h1')  #local
    h2 = net.addHost('h2', serverIp=remote, user=username)
    s1 = net.addSwitch('s2')  #local
    net.addLink(s1, h1)
    net.addLink(s1, h2)

    c0 = net.addController('c0')

    net.start()
    with capsys.disabled():
        for node in c0, h1, h2, s1:
            print('Node', node, 'is running on',
                  node.cmd('hostname').strip(), '\n')
    assert net.pingAll() == 0


def test_local_remote_switches(capsys):
    """
       Test connectivity between local and remote host local and remote switches
       :param capsys:  just capture the std(out/err)
       :return:
       """
    remote = "mininet_host"
    username = "ubuntu"
    net = Mininet(host=RemoteHost, switch=RemoteOVSSwitch, link=RemoteLink)
    c0 = net.addController('c0')
    h1 = net.addHost('h1') #local
    h2 = net.addHost('h2', server=remote, user=username)
    s1 = net.addSwitch('s1')  #local
    s2 = net.addSwitch('s2', server=remote)

    net.addLink(h1, s1)
    net.addLink(s1, s2)
    net.addLink(h2, s2)
    net.start()
    with capsys.disabled():
        for node in c0, h1, h2, s1, s2:
            print('Node', node, 'is running on',
                  node.cmd('hostname').strip(), '\n')
    assert net.pingAll() == 0
