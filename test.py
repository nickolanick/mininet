from hostnet import RemoteLink, RemoteNode, RemoteHost
from mininet.net import Mininet
import pytest


def test_create_host():
    remote = "localhost"
    username = "tymchenko"
    remoteNode = RemoteNode("h1", remote, username)
    # assert remoteNode.cmd('pwd') == "/home/ubuntu\r\n"
    assert remoteNode.cmd('pwd') == "/home/tymchenko/PycharmProjects/mininet_\r\n"


def test_link(capsys):
    remote = "localhost"
    username = "tymchenko"
    net = Mininet(host=RemoteHost, link=RemoteLink)
    h1 = net.addHost('h1')
    h2 = net.addHost('h2', serverIp=remote, user=username)
    h3 = net.addHost('h3', serverIp=remote, user=username)
    net.addLink(h1, h2)
    net.start()
    with capsys.disabled():
        print("Test connectivity between h1 and h3 (not connected)")
        assert net.ping([h1, h3]) == 100
        print("Done\nTest connectivity between h1 and h2 (connected)")
        assert net.ping([h1, h2]) == 0
        print('Done')
    # net.stop()
