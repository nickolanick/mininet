## HostNet

Fork of the famous Mininet network emulator and  supports external HW/VM router in emulated network topologies.
You can use classes RemoteNode, RemoteHost, RemoteLink, RemoteOVSSwitch in your custom topo.

### Requirements
* Python 3.7
* Pytest 5.4.3
* Mininet 2.3.0d6

### Installation
1. Clone this repo
2. Build Topologies as in original Mininet

### Testing
```sh
$ sudo python3.7 -m pytest test_net.py::<function to test>
```
| Functions | Description |
| ------ | ------ |
| test_remote_host | Create remote host and test command execution |
| test_link | Create local and remote hosts and check connectivity |
| test_local_switch | Create local and remote hosts and check connectivity via local switch |
| test_local_remote_switches | Create both local and remote hosts and switches and test connectivity |

If you see `Error creating interface pair` try the following command and rerun
```sh
 sudo mn -c
```

### Mininet: Rapid Prototyping for Software Defined Networks
========================================================  
*The best way to emulate almost any network on your laptop!*

Mininet 2.3.0d6

Original Mininet [repo](https://github.com/mininet/mininet)




