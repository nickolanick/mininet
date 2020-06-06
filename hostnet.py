#!/usr/bin/python3
from mininet.node import Node, Host, OVSSwitch, Controller
from mininet.link import Link, Intf
from mininet.net import Mininet
from mininet.util import quietRun, errRun
from subprocess import Popen, PIPE, STDOUT
import os


class RemoteNode(Node):

    ssh_command = ['ssh','-o', 'ForwardAgent=yes', '-tt']

    def __init__(self,name,serverIp="localhost",user=None,**kwargs):
        self.remoteHost=False
        if serverIp!="localhost":
            self.remoteHost=True
        self.ssh_command.extend([F"{user}@{serverIp}"])
        Node.__init__(self,name, **kwargs )
        

    def startShell( self, *args, **kwargs ):
        "Start a shell process for running commands"

        if self.remoteHost: 
            kwargs.update( mnopts='-c')
        Node.startShell(self,*args, **kwargs )
        self.sendCmd( 'echo $$' )
        self.finishInit()

    def finishInit( self ):
        self.pid = int( self.waitOutput() )

    def _popen(self,cmd,**params):
        "We overide default popen, so that we can extend the passed cmd with our ssh prefix"

        cmd = self.ssh_command+["sudo"]+cmd
        popen = Node._popen(self,cmd, **params )

        return popen

class RemoteHost(RemoteNode):
    pass

class RemoteLink( Link ):
    def __init__(self,node1, node2,**kwargs):
        Link.__init__(self,node1,node2)
    def makeIntfPair( self, intfname1, intfname2, addr1=None, addr2=None,node1=None, node2=None, deleteIntfs=True   ):
        pass
    def makeTunnel( self, node1, node2, intfname1, intfname2, addr1=None, addr2=None ):
        pass
    def moveIntf( intf, node ):
        pass
def basicTest():
    remote   = "mininet_host"
    username = "mininet"
    link     = RemoteLink
    net = Mininet( host=RemoteHost, link=link )
    h1 = net.addHost( 'h1')
    h2 = net.addHost( 'h2', serverIp=remote,user=username)
    net.addLink( h1, h2 )
    net.start()
    net.pingAll()
    net.stop()

def prototypeTest():
    remote   = "mininet_host"
    username = "mininet"
    remoteNode = RemoteNode("h1",remote,username)
    print(remoteNode.cmd('ls'))
if __name__=="__main__":
    prototypeTest()
