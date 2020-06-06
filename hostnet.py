#!/usr/bin/python3
from mininet.node import Node, Host, OVSSwitch, Controller
from mininet.link import Link, Intf
from mininet.net import Mininet
from mininet.util import quietRun, errRun
from subprocess import Popen, PIPE, STDOUT
import os


class RemoteNode(Node):
	pass

class RemoteHost(RemoteNode):
	pass

class RemoteLink( Link ):
	pass


def basicTest():
	net = Mininet( host=RemoteHost, link=link )
	h1 = net.addHost( 'h1')
	h2 = net.addHost( 'h2', server=remote )
	net.addLink( h1, h2 )
	net.start()
	net.pingAll()
	net.stop()


if __name__=="__main__":
	basicTest()
