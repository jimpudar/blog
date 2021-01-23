Title: Adventures in Rolling Your Own Router: Part V
Date: 2021-01-22
Category: Development
Tags: router, linux, debian, firewall, nftables
Slug: router-part-5
Author: Jim Pudar
Summary: Building a firewall with nftables
Status: published

<!-- markdownlint-disable line-length no-trailing-punctuation -->

In my [previous post]({filename}/debian-router-4.md), I set up NAT using
`nftables`. In this post, I'll use `nftables` to set up a firewall.

In my current router, I have disabled IPv6 entirely, so no IPv6 packets can
enter or leave my network. I do want to start experimenting with IPv6, so I
will not want to take this strategy for the new firewall.

Looking again at the `netfilter` diagram, we can see we are mostly interested
in the `forward` and `input` chains of the `filter` table. The former will
allow us to filter packets destined for the LAN, and the latter packets
destined for the router itself.

![Netfilter diagram]({photo}router/netfilter-diagram.jpg)

Instead of building the rules using the `nft` CLI, we can just modify
`/etc/nftables.conf`. I've added comments in the file to explain what each
rule is for.

```text
jmp@debrouter:~$ cat /etc/nftables.conf
#!/usr/sbin/nft -f

flush ruleset

table ip filter {
    # applies to packets which are traveling through this machine
    chain forward {
        type filter hook forward priority 0; policy drop;

        # allow packets leaving the network
        oifname extern0 accept

        # allow replies
        iifname extern0 ct state related,established accept
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # drop invalid packets early
        ct state invalid drop

        # accept replies
        ct state related,established accept

        # open loopback interface
        iif lo accept

        # accept ICMP and IGMP
        ip protocol icmp accept
        ip protocol igmp accept

        # allow SSH from all interfaces
        tcp dport ssh accept

        # allow Mosh from all interfaces
        udp dport { 60000-61000 } accept

        # allow DNS queries from the LAN
        iifname intern0 tcp dport 53 accept
        iifname intern0 udp dport 53 accept

        # allow traceroute
        udp dport { 33434-33524 } accept
    }
}

table ip6 filter {
    chain forward {
        type filter hook forward priority 0; policy drop;

        # for now, we will not forward IPv6 traffic.
    }

    chain input {
        type filter hook forward priority 0; policy drop;

        # drop invalid packets early
        ct state invalid drop

        # accept replies
        ct state related,established accept

        # accept ICMPv6
        ip6 nexthdr icmpv6 accept
    }
}

table ip nat {
    chain postrouting {
        type nat hook postrouting priority 100; policy accept;

        # perform NAT for packets coming from the LAN and going to the Internet
        ip saddr 192.168.77.0/24 oifname extern0 masquerade
    }
}
```

Now, I can `mosh` to and `ping6` the router from the external interface:

```text
jmp@archimedes ~ % mosh 192.168.10.17
jmp@192.168.10.17's password:

jmp@archimedes ~ % ping6 -I en0 fe80::5054:ff:fec7:caa6
PING6(56=40+8+8 bytes) fe80::874:cee0:e328:8115%en0 --> fe80::5054:ff:fec7:caa6
16 bytes from fe80::5054:ff:fec7:caa6%en0, icmp_seq=0 hlim=64 time=0.820 ms
16 bytes from fe80::5054:ff:fec7:caa6%en0, icmp_seq=1 hlim=64 time=0.504 ms
16 bytes from fe80::5054:ff:fec7:caa6%en0, icmp_seq=2 hlim=64 time=0.544 ms
16 bytes from fe80::5054:ff:fec7:caa6%en0, icmp_seq=3 hlim=64 time=0.442 ms
```

In the next post, I'll install PiHole for DNS and DHCP service.
