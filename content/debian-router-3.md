Title: Adventures in Rolling Your Own Router: Part III
Date: 2021-01-18
Category: Development
Tags: router, arch, linux, debian, pihole
Slug: router-part-3
Author: Jim Pudar
Summary: Virtual router testing
Status: published

<!-- markdownlint-disable line-length no-trailing-punctuation -->

In my [previous post]({filename}/debian-router-2.md), I described my plan for
the new router. In this post, I'll create a virtual router, LAN, and client in
order to test out my plan for the Debian router.

This is easy to accomplish using Cockpit on RHEL, but you can do this on any
Linux distribution.

# Debian Installation

I downloaded the net installer for Debian 10.7 "buster" and created the first
VM called `debrouter` with two network interfaces. The first interface is
bridged with my RHEL server's Ethernet interface and will get its own IP
address via DHCP on my real LAN in the `192.168.10.0/24` block. The second
network interface is connected to the virtual LAN `privatelan`. These will be
the WAN and LAN ports respectively.

At the software selection page, I have disabled all but the SSH server. The
fewer packages installed, the better!

After the installation is complete, we can ssh into the new VM.

# Set Up sudo

Since we didn't install anything, we unsurprisingly don't have `sudo`.

```bash
jmp@debrouter:/etc/network$ su -
Password:
root@debrouter:~# apt install sudo
root@debrouter:~# usermod -aG sudo jmp
```

Now after logging out and logging back in again, `jmp` can use `sudo`.

# Network Interface Configuration

We will first set up some configuration for `systemd-networkd`, then we will
disable the default `networking` service.

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

## Disable networking and Enable systemd-networkd

By default, Debian uses the `/etc/network/interfaces` configuration file
and the systemd unit `networking.service` to configure the network interfaces
on boot.

Since we want `systemd-networkd` to control this instead, we need to rename
the configuration file and [disable the
service](https://wiki.debian.org/SystemdNetworkd#Setting_up_Systemd-Networkd).

Note: the Debian docs don't suggest disabling the service, but I haven't had
any issues doing so.

```text
jmp@debrouter:~$ sudo mv /etc/network/interfaces /etc/network/interfaces.save
jmp@debrouter:~$ sudo systemctl disable networking
```

Be careful not to _stop_ the service yet, or else our interface will go down
and we will lose the SSH session.

Now, we can enable `systemd-networkd.service`.

```text
jmp@debrouter:~$ sudo systemctl enable systemd-networkd
```

## Finishing Up

Now we can reboot and see our network interfaces are configured correctly! Our
`extern0` interface got a dynamic address `192.168.10.18` (on my real LAN) and
the `intern0` interface has the static address `192.168.77.1` as requested.

```text
jmp@debrouter:~$ ip ad
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: extern0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 52:54:00:c7:ca:a6 brd ff:ff:ff:ff:ff:ff
    inet 192.168.10.18/24 brd 192.168.10.255 scope global dynamic extern0
       valid_lft 3567sec preferred_lft 3567sec
    inet6 fe80::5054:ff:fec7:caa6/64 scope link
       valid_lft forever preferred_lft forever
3: intern0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 52:54:00:e3:bb:78 brd ff:ff:ff:ff:ff:ff
    inet 192.168.77.1/24 brd 192.168.77.255 scope global intern0
       valid_lft forever preferred_lft forever
    inet6 fe80::5054:ff:fee3:bb78/64 scope link
       valid_lft forever preferred_lft forever
```

# Where is nftables?

At this point, because we added `IPMasquerade=true` in our LAN network file,
we should have some `nftables` rules automatically added. However, to my
suprise, `nftables` is not installed by default in Debian 10. Furthermore,
some `iptables-legacy` rules get created instead!

```text
jmp@debrouter:~$ su -
Password:
root@debrouter:~# nft
-bash: nft: command not found
root@debrouter:~# iptables-legacy-save
# Generated by iptables-save v1.8.2 on Mon Jan 18 00:18:25 2021
*nat
:PREROUTING ACCEPT [61:10854]
:INPUT ACCEPT [57:9808]
:OUTPUT ACCEPT [6:447]
:POSTROUTING ACCEPT [6:447]
-A POSTROUTING -s 192.168.77.0/24 -j MASQUERADE
COMMIT
# Completed on Mon Jan 18 00:18:25 2021
```

Looks like the version of `systemd` which ships with Debian buster is out of
date. Let's install the latest `systemd` from `buster-backports`...

```text
jmp@debrouter:~$ sudo sh -c 'echo "deb http://deb.debian.org/debian buster-backports main" >>/etc/apt/sources.list'
jmp@debrouter:~$ sudo apt update
jmp@debrouter:~$ sudo apt -t buster-backports install systemd
```

Reboot, aaaand... nope. No dice. Looking in the [commit
history](https://github.com/systemd/systemd/commit/715a70e7218710d6a6c033e9157bf97fdf5d8ede),
it seems like the `nftables` backend hasn't even been released yet.

For the time being, let's continue with the legacy rules, but we will need to
replace these later on when we install `nftables`.

# Testing With A Client

At this point, a client should be able to connect to the internal network with
a static IP and connect to the Internet through our virtual router.

I'll now set up another Debian VM called `debclient`, this time with only one
interface connected to the `privatelan` network.

During the installation process, automatic network configuration fails
(expectedly, because there is no DHCP server) so we can manually set up a
static IP of `192.168.77.2`, netmask `255.255.255.0`, and gateway
`192.168.77.1`. Since we don't have a nameserver set up yet, I'm using
Google's DNS `8.8.8.8` since it's easy to remember.

After the installation is complete, I set up `tcpdump` to listen for ICMP
packets on both of the router's interfaces and then pinged Google's DNS server
from the client.

```text
jmp@debrouter:~$ sudo tcpdump -i any icmp
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on any, link-type LINUX_SLL (Linux cooked), capture size 262144 bytes
00:40:17.258834 IP 192.168.77.2 > dns.google: ICMP echo request, id 434, seq 1, length 64
00:40:17.258872 IP debrouter.crbj.io > dns.google: ICMP echo request, id 434, seq 1, length 64
00:40:17.276588 IP dns.google > debrouter.crbj.io: ICMP echo reply, id 434, seq 1, length 64
00:40:17.276607 IP dns.google > 192.168.77.2: ICMP echo reply, id 434, seq 1, length 64
```

Looks like it's routing packets!

In the next post, I'll investigate what's going on with `nftables` and start
working on the firewall.
