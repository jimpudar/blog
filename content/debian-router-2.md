Title: Adventures in Rolling Your Own Router: Part II
Date: 2021-01-16
Category: Development
Tags: router, arch, linux, debian, pihole
Slug: router-part-2
Author: Jim Pudar
Summary: Plans for the new router
Status: published

<!-- markdownlint-disable no-trailing-punctuation -->
# What OS?
<!-- markdownlint-enable no-trailing-punctuation -->

While PiHole [can](https://aur.archlinux.org/packages/pi-hole-ftl/) be
installed directly on Arch Linux or be run in a Docker container, I feel it is
safer to use an officially supported OS. My choices are Debian, Ubuntu,
Fedora, or CentOS.

I don't want to use Ubuntu because even in `ubuntu-server` there are more
bells and whistles than I need.

Fedora is out, because I am interested in long term stability. CentOS would be
a good option if it wasn't
[EOL](https://wiki.centos.org/Manuals/ReleaseNotes/CentOSStream) at the end of
2021.

This leaves Debian, an OS which I do not have much experience with.

<!-- markdownlint-disable no-trailing-punctuation -->
# What Should it Do, and How?
<!-- markdownlint-enable no-trailing-punctuation -->

## NAT Routing

The router needs to not only forward packets between clients on the LAN and
the Internet, it also needs to perform Network Address Translation because in
my network only the router itself has a public IP address.

NAT can be enabled with `systemd.network` using the `IPMasquerade` flag.

Based on the [man
page](https://www.freedesktop.org/software/systemd/man/systemd.network.html),
just enabling `IPMasquerade` on the LAN interface _should_ be enough to also
enable packet forwarding (`IPForward`). We will see if that's really the case.

Since we want to use `nftables` instead of `iptables` on this system,
`systemd` [_should_](https://github.com/systemd/systemd/issues/13307) be
modifying `nftables` rather than using legacy `iptables`. See also
[here](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=934584).

## PiHole DNS

I want [PiHole](https://pi-hole.net) to run on the router. This is basically
[`dnsmasq`](https://linux.die.net/man/8/dnsmasq) with some filter lists and a
fancy GUI.

PiHole is supported on Debian, so we should be able to just install it using
the installer script. However, the [installation instructions
mention](https://docs.pi-hole.net/main/prerequisites/#ip-addressing) that it
will install `dhcpcd5` and modify `/etc/dhcpcd.conf` to assign a static IP
address. We don't want this because we will be using `systemd.networkd` for
interface management.

This means that I will potentially need to modify the installer script to skip
this.

## DHCP Server

The router should also run a DHCP server, optionally providing "static IPs" to
known clients based on MAC address.

Since PiHole contains `dnsmasq`, we can just enable the DHCP server built in
to `pihole-FTL.service`.

## Firewall

All incoming traffic except SSH and [Mosh](https://mosh.org) should be
blocked. We need [connection
tracking](https://en.wikipedia.org/wiki/Stateful_firewall) to allow clients to
communicate with Internet hosts.

I've never used [`nftables`](https://wiki.debian.org/nftables), but since this
is the [immediate future](https://lwn.net/Articles/747551/) I'll take this as
an opportunity to learn.

In the next post, I'll set up some VMs and try setting this up before doing it
on my physical network.
