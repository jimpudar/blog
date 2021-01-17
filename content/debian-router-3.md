Title: Adventures in Rolling Your Own Router: Part III
Date: 2021-01-16
Category: Development
Tags: router, arch, linux, debian, pihole
Slug: router-part-3
Author: Jim Pudar
Summary: Virtual router testing
Status: draft

<!-- markdownlint-disable line-length -->
In this post, I'll create a virtual router, LAN, and client in order to test
out my plan for the Debian router.

I have VMWare Fusion Pro, so it's easy to create a private virtual network
`vmnet3` and a couple of VMs.

# Debian Installation

I downloaded the net installer for Debian 10.7 "buster" and created the first
VM called `debrouter` with two network interfaces. The first interface is
bridged with my Mac's Ethernet interface and will get its own IP address via
DHCP on my real LAN in the `192.168.10.0/24` block. The second network
interface is connected to the virtual LAN `vmnet3`. These will be the WAN and
LAN ports respectively.

While it's a pain in the ass to connect a monitor and keyboard to my physical
router, from what I've read about headless installation it should be easier.

In the VM, I'm starting off with the graphical installer. I'm setting up
encrypted LVM since PiHole will be storing all sorts of PII. I like having
separate `/home`, `/var`, and `/tmp` partitions, so I chose that option.

Note: encrypted LVM is probably a bad choice since we are running headless and
want the system to recover after power loss!

The Debian installer has come a _long_ way since I last used it. Ironically,
it's even easier than Ubuntu's these days!

At the software selection page, I have disabled all but the SSH server. The
fewer packages installed, the better!

Finally after the installation is complete, we can ssh into the new VM.

# Set Up `sudo`

Since we didn't install anything, we unsurprisingly don't have `sudo`.

```bash
jmp@debrouter:/etc/network$ su -
Password:
root@debrouter:~# apt install sudo
root@debrouter:~# usermod -aG sudo jmp
```

Now after logging out and logging back in again, `jmp` can use `sudo`.

# Network Interface Configuration

## Disable `networking` and Enable `systemd-networkd`

By default, Debian uses the `/etc/network/interfaces` configuration file
and the systemd unit `networking.service` to configure the network interfaces
on boot.

```text
jmp@debrouter:~$ cat /etc/network/interfaces
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug ens33
iface ens33 inet dhcp
```

Since we want `systemd-networkd` to control this instead, we need to rename
the configuration file and [disable the
service](https://wiki.debian.org/SystemdNetworkd#Setting_up_Systemd-Networkd).

Note: the Debian docs don't suggest disabling the service. We will see if
doing so causes any problems.

```text
jmp@debrouter:~$ sudo mv /etc/network/interfaces /etc/network/interfaces.save
jmp@debrouter:~$ sudo systemctl disable networking
Synchronizing state of networking.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install disable networking
Removed /etc/systemd/system/multi-user.target.wants/networking.service.
Removed /etc/systemd/system/network-online.target.wants/networking.service.
```

Be careful not to _stop_ the service yet, or else our interface will go down
and we will lose the SSH session.

Now, we can enable `systemd-networkd.service`.

```text
jmp@debrouter:~$ sudo systemctl enable systemd-networkd
Created symlink /etc/systemd/system/dbus-org.freedesktop.network1.service → /lib/systemd/system/systemd-networkd.service.
Created symlink /etc/systemd/system/multi-user.target.wants/systemd-networkd.service → /lib/systemd/system/systemd-networkd.service.
Created symlink /etc/systemd/system/sockets.target.wants/systemd-networkd.socket → /lib/systemd/system/systemd-networkd.socket.
Created symlink /etc/systemd/system/network-online.target.wants/systemd-networkd-wait-online.service → /lib/systemd/system/systemd-networkd-wait-online.service.
```

## Rename Network Interfaces

I like to give logical persistent names for each network interface. We can do
this using
[`systemd.link`](https://manpages.debian.org/buster/udev/systemd.link.5.en.html).

First, we need to get the MAC addresses of each interface:

```text
jmp@debrouter:~$ ip link
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether 00:0c:29:5e:8e:fa brd ff:ff:ff:ff:ff:ff
3: ens34: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 00:0c:29:5e:8e:04 brd ff:ff:ff:ff:ff:ff
```

Now, we can create a `.link` file for each interface with our desired names:

```text
jmp@debrouter:~$ cat /etc/systemd/network/10-extern0.link /etc/systemd/network/20-intern0.link
[Match]
MACAddress=00:0c:29:5e:8e:fa

[Link]
Name=extern0
[Match]
MACAddress=00:0c:29:5e:8e:04

[Link]
Name=intern0
```

## Configure Network Interfaces

Finally we can define our
[`.network`](https://www.freedesktop.org/software/systemd/man/systemd.network.html)
files:

```text
jmp@debrouter:~$ cat /etc/systemd/network/external.network
[Match]
Name=extern0

[Network]
DHCP=ipv4

jmp@debrouter:~$ cat /etc/systemd/network/internal.network
[Match]
Name=intern0

[Network]
Address=192.168.77.1/24
IPMasquerade=true
```

Now we can reboot and see our network interfaces are configured correctly! Our
`extern0` interface got a dynamic address `192.168.10.20` (on my real LAN) and
the `intern0` interface has the static address `192.168.77.1` as requested.

```text
jmp@debrouter:~$ ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: extern0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 00:0c:29:5e:8e:fa brd ff:ff:ff:ff:ff:ff
    inet 192.168.10.20/24 brd 192.168.10.255 scope global dynamic extern0
       valid_lft 3568sec preferred_lft 3568sec
    inet6 fe80::20c:29ff:fe5e:8efa/64 scope link
       valid_lft forever preferred_lft forever
3: intern0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 00:0c:29:5e:8e:04 brd ff:ff:ff:ff:ff:ff
    inet 192.168.77.1/24 brd 192.168.77.255 scope global intern0
       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe5e:8e04/64 scope link
       valid_lft forever preferred_lft forever
```

# Testing With A Client

At this point, a client should be able to connect to the internal network with
a static IP and connect to the Internet through our virtual router.

I'll now set up another Debian VM called `debclient`, this time with only one
interface connected to the `vmnet3` network.

During the installation process, automatic network configuration fails
(expectedly, because there is no DHCP server) so we can manually set up a
static IP of `192.168.77.2`, netmask `255.255.255.0`, and gateway
`192.168.77.1`. Since we don't have a nameserver set up yet, I'm using
Google's DNS `8.8.8.8` since it's easy to remember.

Once we get to a command line, nothing works. We can't connect to the
Internet, although we _can_ ping our virtual gateway.

Looks like the version of `systemd` which ships with Debian buster is out of
date: `systemd-networkd`'s `IPMasquerade` functionality is actually modifying
the `iptables-legacy` tables instead of using `nftables`. (Hmm.. CentOS Stream
is starting to sound nice right about now!)
