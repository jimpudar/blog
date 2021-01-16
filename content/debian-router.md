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
