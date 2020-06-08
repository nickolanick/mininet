#!/usr/bin/python3

from mininet.examples.clustercli import CLI
from mininet.log import setLogLevel, debug, info, error
from mininet.node import Node, Host, OVSSwitch, Controller
from mininet.link import Link, Intf
from mininet.net import Mininet
from mininet.util import quietRun, errRun
from subprocess import Popen, PIPE, STDOUT

import os
import sys
import re

from itertools import groupby
from operator import attrgetter
from distutils.version import StrictVersion

def findUser():
   """ Try to return logged-in (usually non-root) user"""
   return (
            os.environ.get( 'SUDO_USER', False ) or
            ( quietRun( 'who am i' ).split() or [ False ] )[ 0 ] or
            quietRun( 'whoami' ).strip() )

class RemoteMixin(object):
    """ This node can be either remote or local, IPC is done via ssh """
    ssh_command = ['ssh','-o', 'ForwardAgent=yes', '-tt']

    def __init__(self,name,serverIp="localhost",user=None,**kwargs):
        """ Initialise Node and determine if is local or remote """
        self.remoteHost = False
        self.serverIp   = serverIp
        self.server    = serverIp
        self.user       = user if user else findUser()

        if serverIp!="localhost":
            self.remoteHost=True
            self.dest = '%s@%s' % ( self.user, self.serverIp )
            self.ssh_command.extend([F"{user}@{serverIp}"])

        super(RemoteMixin,self).__init__(name, **kwargs )
        
    def rpopen( self, *cmd, **opts ):
        """ Return a Popen object on underlying server in root namespace """

        params = { 'stdin': PIPE,
                   'stdout': PIPE,
                   'stderr': STDOUT,
                   }
        params.update( opts )

        return self._popen( *cmd, **params )

    def rcmd( self, *cmd, **opts):
        """ rcmd: run a command on underlying server in root namespace """

        popen = self.rpopen( *cmd, **opts )
        result = ''

        while True:
            poll = popen.poll()
            stdout = popen.stdout.read().decode("utf-8") 
            result += stdout 
            if poll is not None:
                break
        return result

    def startShell( self, *args, **kwargs ):
        """ Start a shell process for running commands """

        if self.remoteHost: 
            kwargs.update( mnopts='-c')

        super(RemoteMixin, self).startShell(*args, **kwargs )
        self.sendCmd( 'echo $$' )
        self.pid = int( self.waitOutput() )

    def _popen(self,cmd,sudo = True,tt=True, **params):
        """ We overide default popen, so that we can extend the passed cmd with our ssh prefix """

        if type( cmd ) is str:
            cmd = cmd.split(" ")

        if sudo:
            cmd = ["sudo"] + cmd 

        if self.remoteHost:
            if tt:
                cmd = self.ssh_command + cmd
            else:
                sshcmd = list( self.ssh_command)
                sshcmd.remove( '-tt' )
                cmd = sshcmd + cmd

        popen = super(RemoteMixin,self)._popen(cmd, **params )
        return popen
    
    def popen( self, *args, **kwargs ):
        """ Disable -tt """

        return super(RemoteMixin,self).popen( *args, tt=False, **kwargs )

    

class RemoteNode(RemoteMixin,Node):
    pass
class RemoteHost(RemoteNode):
    pass

class RemoteOVSSwitch( RemoteMixin, OVSSwitch ):
    "Remote instance of Open vSwitch"

    OVSVersions = {}

    def __init__( self, *args, **kwargs ):
        # No batch startup yet
        kwargs.update( batch=True )

        super( RemoteOVSSwitch, self ).__init__( *args, **kwargs )

    @classmethod
    def batchStartup( cls, switches, **_kwargs ):
        """ Start up switches """
        key = attrgetter( 'serverIp' )
        for server, switchGroup in groupby( sorted( switches, key=key ), key ):
            info( '(%s)' % server )
            group = tuple( switchGroup )
            switch = group[ 0 ]
            OVSSwitch.batchStartup( group, run=switch.cmd )
        return switches

    @classmethod
    def batchShutdown( cls, switches, **_kwargs ):
        """ Stop switches in per-server batches """
        key = attrgetter( 'serverIp' )
        for server, switchGroup in groupby( sorted( switches, key=key ), key ):
            info( '(%s)' % server )
            group = tuple( switchGroup )
            switch = group[ 0 ]
            OVSSwitch.batchShutdown( group, run=switch.rcmd )
        return switches


class RemoteLink( Link ):
    def __init__(self,node1, node2,**kwargs):
        self.node1 = node1
        self.node2 = node2
        self.tunnel = None
        Link.__init__(self,node1,node2)

    def makeIntfPair( self, intfname1, intfname2, addr1=None, addr2=None,node1=None, node2=None, deleteIntfs=True   ):
        """ Depending on server type create interfaces """

        node1 = self.node1 if node1 is None else node1
        node2 = self.node2 if node2 is None else node2

        server1 = getattr( node1, 'serverIp', 'localhost' )
        server2 = getattr( node2, 'serverIp', 'localhost' )

        if server1 == server2:
            return Link.makeIntfPair( intfname1, intfname2, addr1, addr2, node1, node2, deleteIntfs=deleteIntfs )

        self.tunnel = self.makeTunnel( node1, node2, intfname1, intfname2, addr1, addr2 )

        return self.tunnel
    def stop( self ):
        "Stop this link"
        if self.tunnel:
            self.tunnel.terminate()
            self.intf1.delete()
            self.intf2.delete()
        else:
            Link.stop( self )
        self.tunnel = None

    #@classmethod
    def moveIntf(self, intf, node ):
        """ Move remote interface from root ns to node """

        intf = str( intf )
        cmd = f'ip link set {intf} netns {node.pid}'
        result = node.rcmd( cmd )

        return True

    def makeTunnel( self, node1, node2, intfname1, intfname2, addr1=None, addr2=None ):
        """ Create 2nd layer ssh tunnel """

        create_tap = "ip tuntap add dev tap9 mode tap user "

        if node2.serverIp == 'localhost':
            return self.makeTunnel( node2, node1, intfname2, intfname1, addr2, addr1 )

        for node in node1, node2:
                node.rcmd(create_tap+node.user)

        dest          = f'{node2.user}@{node2.serverIp}'
        cmd           = [ 'ssh', '-n', '-o', 'Tunnel=Ethernet', '-w', '9:9', dest, 'echo !' ]
        self.cmd      = cmd
        tunnel        = node1.rpopen( cmd, sudo=False )
        tunnel_status = tunnel.stdout.read( 1 ).decode("utf-8") 
        
        #assert tunnel_status=="!"
        
        for node in node1, node2:
            assert self.moveIntf( 'tap9',node)

        for node, intf, addr in ( ( node1, intfname1, addr1 ),( node2, intfname2, addr2 ) ):
            if not addr:
                node.cmd( 'ip link set tap9 name', intf )
            else:
                node.cmd( 'ip link set tap9 name', intf, 'address', addr )

        return tunnel


def basicTest():
    remote   = "mininet_host"
    username = "ubuntu"

    net = Mininet( host=RemoteHost, link=RemoteLink,switch=RemoteOVSSwitch)

    h1 = net.addHost( 'h1')
    h2 = net.addHost( 'h2', serverIp=remote,user=username)

    s1 = net.addSwitch('s2')

    net.addLink( s1, h1 )
    net.addLink( s1, h2 )

    c0 = net.addController( 'c0' )

    net.start()
    net.pingAll()

    CLI( net )
    net.stop()

def prototypeTest():
    remote   = "mininet_host"
    username = "mininet"
    remoteNode = RemoteNode("h1",remote,username)
    remoteNode.cmd('ls')

if __name__=="__main__":
    basicTest()
