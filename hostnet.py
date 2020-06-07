#!/usr/bin/python3
from mininet.examples.clustercli import CLI
from mininet.node import Node, Host, OVSSwitch, Controller
from mininet.link import Link, Intf
from mininet.net import Mininet
from mininet.util import quietRun, errRun
from subprocess import Popen, PIPE, STDOUT
import os

def findUser():
    "Try to return logged-in (usually non-root) user"
    return (
            os.environ.get( 'SUDO_USER', False ) or
            ( quietRun( 'who am i' ).split() or [ False ] )[ 0 ] or
            quietRun( 'whoami' ).strip() )
class RemoteNode(Node):

    ssh_command = ['ssh','-o', 'ForwardAgent=yes', '-tt']

    def __init__(self,name,serverIp="localhost",user=None,**kwargs):
        self.remoteHost = False
        self.serverIp   = serverIp
        self.user       = user if user else findUser()

        if serverIp!="localhost":
            self.remoteHost=True
            self.server = serverIp
            self.dest = '%s@%s' % ( self.user, self.serverIp )
            self.ssh_command.extend([F"{user}@{serverIp}"])
        Node.__init__(self,name, **kwargs )
        
    def rpopen( self, *cmd, **opts ):
        "Return a Popen object on underlying server in root namespace"
        params = { 'stdin': PIPE,
                   'stdout': PIPE,
                   'stderr': STDOUT
                   }
        params.update( opts )
        return self._popen( *cmd, **params )

    def rcmd( self, *cmd, **opts):
        """
           rcmd: run a command on underlying server
           in root namespace
        """
        popen = self.rpopen( *cmd, **opts )

        result = ''
        while True:
            poll = popen.poll()
            stdout = str(popen.stdout.read())
            result += stdout 
            if poll is not None:
                break
        return result

    def startShell( self, *args, **kwargs ):
        "Start a shell process for running commands"

        if self.remoteHost: 
            kwargs.update( mnopts='-c')
        Node.startShell(self,*args, **kwargs )
        self.sendCmd( 'echo $$' )
        self.finishInit()

    def finishInit( self ):
        self.pid = int( self.waitOutput() )

    def _popen(self,cmd,sudo = True,tt=True, **params):
        "We overide default popen, so that we can extend the passed cmd with our ssh prefix"
        if type( cmd ) is str:
            cmd = cmd.split(" ")
        if self.remoteHost:
            cmd = self.ssh_command+["sudo"] +cmd
        else:
            cmd =["sudo"]+cmd
        popen = Node._popen(self,cmd, **params )

        return popen
    def addIntf( self, *args, **kwargs ):
        "Override: use RemoteLink.moveIntf"
        # kwargs.update( moveIntfFn=RemoteLink.moveIntf )
        return Node.addIntf(self,*args, **kwargs )

class RemoteHost(RemoteNode):
    pass

class RemoteLink( Link ):
    def __init__(self,node1, node2,**kwargs):
        self.node1 = node1
        self.node2 = node2
        self.tunnel = None
        Link.__init__(self,node1,node2)

    def makeIntfPair( self, intfname1, intfname2, addr1=None, addr2=None,node1=None, node2=None, deleteIntfs=True   ):
        
        node1 = self.node1 if node1 is None else node1
        node2 = self.node2 if node2 is None else node2
        server1 = getattr( node1, 'server', 'localhost' )
        server2 = getattr( node2, 'server', 'localhost' )
        if server1 == server2:
            return Link.makeIntfPair( intfname1, intfname2, addr1, addr2,
                                      node1, node2, deleteIntfs=deleteIntfs )
        self.tunnel = self.makeTunnel( node1, node2, intfname1, intfname2,
                                       addr1, addr2 )
        return self.tunnel

    @staticmethod
    def moveIntf(intf, node ):
        """Move remote interface from root ns to node
            intf: string, interface
            dstNode: destination Node
            srcNode: source Node or None (default) for root ns"""
        intf = str( intf )
        cmd = 'ip link set %s netns %s' % ( intf, node.pid )
        result = node.rcmd( cmd )
        return True

    def makeTunnel( self, node1, node2, intfname1, intfname2, addr1=None, addr2=None ):

        create_tap = "ip tuntap add dev tap9 mode tap user "
        if node2.server == 'localhost':
            return self.makeTunnel( node2, node1, intfname2, intfname1, addr2, addr1 )

        for node in node1, node2:
                node.rcmd(create_tap+node.user)

        dest = '%s@%s' % ( node2.user, node2.serverIp )
        cmd = [ 'ssh', '-n', '-o', 'Tunnel=Ethernet', '-w', '9:9',
                dest, 'echo !' ]
        self.cmd = cmd

        tunnel = node1.rpopen( cmd, sudo=False )
        ch = tunnel.stdout.read( 1 )

        #assert ch=="!"

        for node in node1, node2:
            if not self.moveIntf( 'tap9',node):
                raise Exception( 'interface move failed on node %s' % node )

        for node, intf, addr in ( ( node1, intfname1, addr1 ),
                                  ( node2, intfname2, addr2 ) ):
            if not addr:
                result = node.cmd( 'ip link set tap9 name', intf )
            else:
                result = node.cmd( 'ip link set tap9 name', intf,
                                   'address', addr )
        return tunnel



def basicTest():
    remote   = "mininet_host"
    username = "mininet"
    link     = RemoteLink
    net = Mininet( host=RemoteHost, link=RemoteLink)
    h1 = net.addHost( 'h1')
    h2 = net.addHost( 'h2', serverIp=remote,user=username)

    net.addLink( h1, h2 )
    net.start()
    net.pingAll()
    CLI( net )
    net.stop()

def prototypeTest():
    remote   = "mininet_host"
    username = "mininet"
    remoteNode = RemoteNode("h1",remote,username)
    print(remoteNode.cmd('ls'))

if __name__=="__main__":
    basicTest()
