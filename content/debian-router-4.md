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
are great instructions on the [nftables
wiki](https://wiki.nftables.org/wiki-nftables/index.php/Performing_Network_Address_Translation_(NAT)).

First, we need to add a `nat` table.

```text
jmp@debrouter:~$ sudo nft add table nat
```

Next, we need a `postrouting` chain.

```text
jmp@debrouter:~$ sudo nft 'add chain nat postrouting { type nat hook postrouting priority 100 ; }'
```

Finally, we can add a rule to the chain to enable `masquerade`.

```text
jmp@debrouter:~$ sudo nft add rule nat postrouting masquerade
```

That's all it takes! We can now ping servers on the Internet from `debclient`
again.

# Persistence of nftables Ruleset

We want these rules to survive the next reboot, so we can add them to
`/etc/nftables.conf`.

```text
jmp@debrouter:~$ cat /etc/nftables.conf
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy accept;
    }

    chain forward {
        type filter hook forward priority 0; policy accept;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
table ip nat {
    chain postrouting {
        type nat hook postrouting priority 100; policy accept;
        masquerade;
    }
}
```

In the next post, we will create a simple firewall using `nftables`.
