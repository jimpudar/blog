Title: Adventures in Rolling Your Own Router: Part IV
Date: 2021-01-19
Category: Development
Tags: router, linux, debian, pihole, firewall, nftables
Slug: router-part-4
Author: Jim Pudar
Summary: Using nftables for NAT on the virtual router
Status: published

<!-- markdownlint-disable line-length no-trailing-punctuation -->

In my [previous post]({filename}/debian-router-3.md), I created a virtual
router, LAN, and client in order to test out my plan for the Debian router. In
this post, I'll set up NAT using `nftables`.

# Installing nftables

As I discovered in the last post, Debian Buster apparently doesn't come with
`nftables` installed, but instead has an `iptables-nft` shim layer on top of
the `nf_tables` kernel subsystem that accepts regular `iptables` rule syntax.
It also comes with `iptables-legacy` that you can use the `alternatives`
system to switch to. The details of this are all laid out in the
[wiki](https://wiki.debian.org/nftables).

To get started with `nftables` we just need to start and enable it:

```text
jmp@debrouter:~$ sudo apt install nftables
jmp@debrouter:~$ sudo systemctl enable nftables
```

# Replacing iptables-legacy Rules

Since setting `IPMasquerade=true` in `/etc/systemd/network/internal.network`
caused `systemd-networkd` to create `iptables-legacy` rules, we need to make
a change to that file.

```text
jmp@debrouter:~$ cat /etc/systemd/network/internal.network
[Match]
Name=intern0

[Network]
Address=192.168.77.1/24
IPForward=ipv4

# Currently systemd-networkd uses iptables-legacy.
# Masquerade is manually configured with nftables.
# IPMasquerade=true
```

After a reboot, the `iptables-legacy` rules are gone.

Now, we need to manually set up masquerading using `nftables` directly. There
are some instructions on the [nftables
wiki](https://wiki.nftables.org/wiki-nftables/index.php/Performing_Network_Address_Translation_(NAT)),
but in general documentation for `nftables` is still sparse. If you're looking
for a good primer on `nftables`, check out [this
video](https://www.youtube.com/watch?v=ouqDHX6HwOo) from the Open Source
Summit.

`nftables` controls `netfilter`. In this regard, it's similar to `iptables`.

![Netfilter diagram]({photo}router/netfilter-diagram.jpg)

Unlike `iptables`, `nftables` does not come with all the `netfilter` default
tables and chains set up. This is for performance reasons - if you don't need
them, they don't get executed. However, this means we need to create the
tables and chains that we do need.

Since `masquerade` is applied in the `postrouting` chain of the `nat` table,
we first need to create the `nat` table.

```text
jmp@debrouter:~$ sudo nft add table nat
```

It looks like this automatically creates this table in the `ip` family which
means chains in this table will apply only to IPV4. This is good, because we
don't need NAT for IPv6.

Next, we need to create the `postrouting` chain.

```text
jmp@debrouter:~$ sudo nft 'add chain nat postrouting { type nat hook postrouting priority 100 ; }'
```

Finally, we can add a rule to the chain to enable `masquerade`.

We specify that only packets originating in the LAN and being sent out on the
external interface should have `masquerade` applied.

```text
jmp@debrouter:~$ sudo nft add rule nat postrouting ip saddr 192.168.77.0/24 oifname extern0 masquerade
```

That's all it takes! We can now ping servers on the Internet from `debclient`
again.

# Persistence of nftables Ruleset

We want these rules to survive the next reboot, so we can add them to
`/etc/nftables.conf`.

```text
#!/usr/sbin/nft -f

flush ruleset

table ip nat {
    chain postrouting {
        type nat hook postrouting priority 100; policy accept;
        ip saddr 192.168.77.0/24 oifname extern0 masquerade;
    }
}
```

In the [next post]({filename}/debian-router-5.md), we will create a simple
firewall using `nftables`.
