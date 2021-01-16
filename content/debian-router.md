Title: Adventures in Building a Debian Router: The Old
Date: 2021-01-16
Category: Development
Tags: router, debian, pihole
Slug: debian-router
Author: Jim Pudar
Summary: Details on my old router configuration
Status: published

I've been rolling my own router / firewall solution for several years now. I
started out using OpenBSD, but even though I loved of `pf` I eventually
switched over to Arch Linux. Throughout all these years, I've been using
PiHole installed on a Raspberry Pi 3 for DNS based ad-blocking.

My Arch based router is getting a little crufty, and my documentation is
sparse (thanks, past me!), so I have decided now is a good time to start from
scratch with Debian, documenting the entire process from start to finish.

The goal is to end up with a Debian based router / firewall running PiHole for
DNS/DHCP and using native systemd services wherever possible. I would also
like the total power drawn by my router / switch / access point to be reduced.

In this first post, I'll describe my current system.

# Hardware

I'll outline everything plugged into my [APC
UPS](https://www.apc.com/shop/us/en/products/APC-Power-Saving-Back-UPS-Pro-1500/P-BR1500G).
The power draw of all these components will determine how long my WiFi stays
online during a power outage.

The current power draw of all the components is about 34W. This gives me about
two and a half hours of runtime.

![Thermal Image of Components]({photo}router/router-front.jpg)

## Router

### Power Supply

The [Seasonic PSU](https://www.amazon.com/gp/product/B073GY89G5) I'm currently
using replaced the older [fanless Seasonic
PSU](https://www.amazon.com/gp/product/B009VV56TO) when the latter developed
some coil whine. The former does have a fan, but it hasn't needed to run since
I got it.

### Motherboard

The motherboard is an [MSI AM1 Mini
ITX](https://www.newegg.com/msi-am1i/p/N82E16813130759). I bought it on Newegg
for $24.99. Apparently the price has since jumped to $297.00 - this board is
probably worth less than _I_ paid for it, so I don't know why the price jumped
so much.

### Processor

It has an [Athlon 5150 Kabini Quad-Core 1.6
GHz](https://www.newegg.com/amd-athlon-5150/p/N82E16819113365?Item=9SIA1N83U90953&Tpk=9SIA1N83U90953)
processor which has a TDP of 25W. The
[heatsink](https://www.amazon.com/gp/product/B00U8PUNH2) I use is massive
overkill for this.

### Network Interfaces

To provide dual Ethernet ports, I used an [Intel
PRO/1000](https://www.amazon.com/gp/product/B000BMZHX2). Aside from running
hot, I've been extremely happy with this card.

### RAM

I cannibalized 8G of RAM from an old machine.

### Disk

I cannibalized a 128G SSD from an old machine.

### Case

I picked the [Cooler Master Elite
130](https://www.amazon.com/gp/product/B00ID2FBU6) Mini-Itx case for its small
form factor.

### Fans

Although this build _can_ run completely fanless without much problem, I use
two [Noctua](https://noctua.at/en/products/fan) fans to keep everything cool.
There is one 120mm fan at the front blowing air over the CPU heatsink and
through the PSU and one 80mm fan pointed directly at the heatsink on the
network card.

## Switch

Based on the heat output, this [Buffalo 16 Port Smart
Switch](https://www.amazon.com/gp/product/B00OLUMLPM) is using a lot of power.
After my most recent cleanup, I'm only using 7 ports so I will be able to
replace this with a smaller 8 port switch that should hopefully reduce power
consumption.

## Access Point

The [UAP-AC-LITE](https://www.amazon.com/gp/product/B017MD6CHM) provides good
signal throughout our entire house. It's plugged in to a [24W PoE
injector](https://www.amazon.com/gp/product/B01DW99IPS).

## Modem

I own, rather than rent, an [Arris
Surfboard](https://www.surfboard.com/products/cable-modems/sb6141/). I only
pay for a 100 Mbps connection, so this device is plenty fast. My only
complaint is that it runs extremely hot.

![Thermal Image of Components]({photo}router/router-back.jpg)

## Raspberry Pi

A slightly older [Raspberry
Pi](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) runs
[PiHole](https://pi-hole.net/). It's plugged in to a high quality USB power
adapter.

## Phillips Hue Hub

If our home network goes down, so does our ability to control our Phillips Hue
lights. That's really annoying, so I also have the [Phillips Hue
Hub](https://www.amazon.com/Philips-Hue-Stand-Alone-Bridge/dp/B016H0QZ7I)
plugged in to the UPS.

# Software

## Arch Linux

I chose Arch Linux for my router because it is the distribution I'm most
comfortable with. I also like that it's a rolling release because I know I'm
always getting all the latest updates.

Most of my setup comes from the Arch Wiki pages
[Router](https://wiki.archlinux.org/index.php/router) and [Simple Stateful
Firewall](https://wiki.archlinux.org/index.php/Simple_stateful_firewall).

The working parts:

- Persistent interface names from `systemd-networkd`
- Network interface configuration with `netctl`
- Packet forwarding enabled with systemd
- NAT with `netfilter` (manually created `iptables` rules)
- No DNS / DHCP servers
- Stateful firewall with `netfilter` (`iptables` rules)
- Persistent `iptables` rules autoloaded with systemd unit `iptables.service`
- Open ports for SSH and [Mosh](https://mosh.org/)
- No password auth. Password protected asymmetric key authentication

The not so great things:

- `netctl` instead of `systemd-networkd`
- Manual NAT / masquerade instead of using `systemd-networkd`
- `iptables` is very difficult for me to understand

My `iptables` rules:

(Note: I seem to have port 53 open for UDP and TCP. I think this is an error,
as my DNS server should only be accessible from inside the LAN. I also
shouldn't have UDP port 67 open. This is what I meant by "crufty"...)

<!-- markdownlint-disable line-length -->
```text
# Generated by iptables-save v1.8.6 on Sat Jan 16 16:01:36 2021
*nat
:PREROUTING ACCEPT [69954:7342094]
:INPUT ACCEPT [2535:152263]
:OUTPUT ACCEPT [5496:362059]
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -o extern0 -j MASQUERADE
-A POSTROUTING -s 192.168.10.0/24 -o extern0 -j MASQUERADE
COMMIT
# Completed on Sat Jan 16 16:01:36 2021
# Generated by iptables-save v1.8.6 on Sat Jan 16 16:01:36 2021
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [60076:6351430]
:TCP - [0:0]
:UDP - [0:0]
:fw-interfaces - [0:0]
:fw-open - [0:0]
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -m conntrack --ctstate INVALID -j DROP
-A INPUT -p icmp -m icmp --icmp-type 8 -m conntrack --ctstate NEW -j ACCEPT
-A INPUT -p udp -m conntrack --ctstate NEW -j UDP
-A INPUT -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -m conntrack --ctstate NEW -j TCP
-A INPUT -p udp -j REJECT --reject-with icmp-port-unreachable
-A INPUT -p tcp -j REJECT --reject-with tcp-reset
-A INPUT -j REJECT --reject-with icmp-port-unreachable
-A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -j fw-interfaces
-A FORWARD -j fw-open
-A FORWARD -j REJECT --reject-with icmp-host-unreachable
-A TCP -p tcp -m tcp --dport 22 -j ACCEPT
-A TCP -p tcp -m tcp --dport 53 -j ACCEPT
-A UDP -p udp -m multiport --dports 60000:61000 -j ACCEPT
-A UDP -p udp -m udp --dport 53 -j ACCEPT
-A UDP -p udp -m udp --dport 67 -j ACCEPT
-A fw-interfaces -i intern0 -j ACCEPT
COMMIT
# Completed on Sat Jan 16 16:01:36 2021
# Generated by iptables-save v1.8.6 on Sat Jan 16 16:01:36 2021
*raw
:PREROUTING ACCEPT [6386246:7485406871]
:OUTPUT ACCEPT [60076:6351430]
-A PREROUTING -m rpfilter --invert -j DROP
COMMIT
# Completed on Sat Jan 16 16:01:36 2021
```
<!-- markdownlint-enable line-length -->

## PiHole

PiHole acts as the DNS and DHCP server. PiHole is some extra stuff on top of
`dnsmasq`. Instead of `dnsmasq.service`, `pihole-FTL.service` is enabled.

Configuration includes the following `dnsmasq` entries:

```text
addn-hosts=/etc/pihole/local.list
addn-hosts=/etc/pihole/custom.list
localise-queries
no-resolv
cache-size=10000
log-queries
log-facility=/var/log/pihole.log
local-ttl=2
log-async
server=208.67.222.222
server=208.67.220.220
interface=eth0
server=/use-application-dns.net/

dhcp-authoritative
dhcp-range=192.168.10.2,192.168.10.254,1h
dhcp-option=option:router,192.168.10.1
dhcp-leasefile=/etc/pihole/dhcp.leases
domain=crbj.io

local=/crbj.io/
expand-hosts
read-ethers
```

This treats any DNS lookups under the domain `crbj.io` as local queries that
should not be forwarded, and ensures that a host like `pihole` also gets
expanded to `pihole.crbj.io`. Furthermore, the `/etc/ethers` file is also read
to find the MAC address -> hostname mapping.

By ensuring that every host on my network is listed in the `/etc/ethers` file
and that there is a corresponding entry for each host in the `/etc/hosts`
file, every host gets a persistently mapped IP address when it requests a DHCP
lease. It's possible to accomplish the same thing using `dhcp-host` entries in
the `dnsmasq` config files, but I like using `/etc/hosts` and `/etc/ethers`
better for aesthetics.

Furthermore, because the PiHole is also the DNS server, I get the added
benefit of being able to do DNS lookups of any host from any other host on the
network without having to modify any of the clients' `/etc/hosts` files.

In my next post, I'll describe my plan for the new router.
