Title: Adventures in Rolling Your Own Router: Part VII
Date: 2021-01-24
Category: Development
Tags: router, linux, debian, pihole, ansible
Slug: router-part-7
Author: Jim Pudar
Summary: Headless Pi-hole installation
Status: published

<!-- markdownlint-disable line-length no-trailing-punctuation -->

In my [previous post]({filename}/debian-router-6.md), I set up an Ansible
playbook to automate the configuration of my Debian router / firewall. In this
post, I'll update the playbook to include the installation of Pi-hole for DNS
and DHCP.

# Pi-hole Installer

At the time of writing this post, Pi-hole is at commit
[cbfb58f7](https://github.com/pi-hole/pi-hole/blob/cbfb58f7a283c2a3e7aad95a834a0287175ccb24/automated%20install/basic-install.sh).
I'll link to line numbers at this commit, but be aware the installer script
will change over time.

The Pi-hole installer is meant to be piped directly from `curl` to `bash`.

```text
curl -sSL https://install.pi-hole.net | bash
```

The installer then runs through a set of interactive prompts using
[whiptail](https://linux.die.net/man/1/whiptail), which allow you to choose an
interface, set a static IP, enable or disable the web UI, etc.

The most concerning thing (for this particular router) the installer does is
[install
`dhcpcd5`](https://github.com/pi-hole/pi-hole/blob/cbfb58f7a283c2a3e7aad95a834a0287175ccb24/automated%20install/basic-install.sh#L354)
which could potentially conflict with `systemd-networkd`. It also will attempt
to set a static IP address on the interface you choose using a [variety of
methods](https://github.com/pi-hole/pi-hole/blob/cbfb58f7a283c2a3e7aad95a834a0287175ccb24/automated%20install/basic-install.sh#L973),
none of which are `systemd-networkd`.

Luckily for us, we can bypass the canned interface probing and the
modification of network configuration using a "secret" argument.
If we pass the [--unattended](https://github.com/pi-hole/pi-hole/blob/cbfb58f7a283c2a3e7aad95a834a0287175ccb24/automated%20install/basic-install.sh#L123)
argument to the installer, the [conditional in the main
function](https://github.com/pi-hole/pi-hole/blob/cbfb58f7a283c2a3e7aad95a834a0287175ccb24/automated%20install/basic-install.sh#L2680)
lets us bypass all the stuff we don't want.

The only catch is that we need to set up [a file which contains
variables](https://github.com/pi-hole/pi-hole/blob/cbfb58f7a283c2a3e7aad95a834a0287175ccb24/automated%20install/basic-install.sh#L52)
so that Pi-hole can configure itself. These variables would normally be
determined by the interactive portion of the installer.

# Installing Pi-hole with Ansible

The first step in automating the installation is codifying the variable file.
This will be yet another template. The password hash is a dummy value; I'll
reset the password before use.

```text
% cat templates/pihole.setupvars.j2
BLOCKING_ENABLED=true
DHCP_ACTIVE=true
DHCP_START={{ dhcp_range_start }}
DHCP_END={{ dhcp_range_end }}
DHCP_ROUTER={{ dhcp_router }}
DHCP_IPv6=
DHCP_rapid_commit=
PIHOLE_DOMAIN={{ local_domain_name }}
DHCP_LEASETIME=24
WEBPASSWORD=ea54268507ae0dac3da1d3057dbc5e870c6223caff753da02032bbc8f82c76b8
PIHOLE_INTERFACE={{ internal_ifname }}
IPV4_ADDRESS={{ ipv4_address_with_netmask }}
IPV6_ADDRESS=
PIHOLE_DNS_1=9.9.9.9
PIHOLE_DNS_2=149.112.112.112
QUERY_LOGGING=true
INSTALL_WEB_SERVER=true
INSTALL_WEB_INTERFACE=true
LIGHTTPD_ENABLED=true
CACHE_SIZE=10000
```

I have a couple of extra lines of configuration for `dnsmasq`, so I will add
one additional template file for those.

```text
% cat templates/dnsmasq.extras.j2
local=/{{ local_domain_name }}/
expand-hosts
read-ethers
```

Now, we can add some tasks to the playbook to install these template files.

```text
    - name: Ensure Pi-hole configuration directory exists
      ansible.builtin.file:
        path: /etc/pihole
        state: directory
        owner: root
        group: root
        mode: '0755'

    - name: Configure Pi-hole installation variables
      ansible.builtin.template:
        src: templates/pihole.setupvars.j2
        dest: /etc/pihole/setupVars.conf
        owner: root
        group: root
        mode: '0644'
      vars:
        internal_ifname: "intern0"
        ipv4_address_with_netmask: "{{ internal_ip }}/{{ internal_netmask }}"
        local_domain_name: "{{ internal_domain }}"
        dhcp_range_start: "{{ dhcp_start }}"
        dhcp_range_end: "{{ dhcp_end}}"
        dhcp_router: "{{ internal_ip }}"

    - name: Ensure dnsmasq configuration directory exists
      ansible.builtin.file:
        path: /etc/dnsmasq.d
        state: directory
        owner: root
        group: root
        mode: '0755'

    - name: Add extra dnsmasq configuration
      ansible.builtin.template:
        src: templates/dnsmasq.extras.j2
        dest: /etc/dnsmasq.d/10-extra.conf
        owner: root
        group: root
        mode: '0644'
      vars:
        local_domain_name: "{{ internal_domain }}"
```

Now, we need to download the Pi-hole installer. I've decided to just grab the
latest version of the installer rather than pin a particular commit. I'm
hoping that the `setupVars.conf` format won't change anytime soon. Because the
installer script is available over HTTPS, I need to install the
`ca-certificates` package before I can download the installer script with the
`get_url` module.

```text
    - name: Install CA certs
      ansible.builtin.apt:
        name: ca-certificates
        state: latest

    - name: Download Pi-hole installer
      get_url:
        url: https://install.pi-hole.net
        dest: /etc/pihole/basic-install.sh
        owner: root
        group: root
        mode: '0700'
```

Finally, I can install Pi-hole. I will also disable and mask the `dhcpcd`
service that Pi-hole installed for me as we don't want this to ever be
inadvertently enabled.

```text
    - name: Install Pi-hole
      command: /etc/pihole/basic-install.sh --unattended

    - name: Completely disable dhcpcd.service
      ansible.builtin.systemd:
        name: dhcpcd.service
        state: stopped
        enabled: no
        masked: yes
```

Two additional `nftables` rules need to be added to allow the use of DHCP and
HTTP from the LAN interface.

```text
        # allow DHCP from the LAN
        iifname {{ internal_ifname }} udp dport { 67,68 } accept

        # allow HTTP from the LAN for Pi-hole admin console
        iifname {{ internal_ifname }} tcp dport http accept
```

I'll need to supply my `/etc/ethers` and `/etc/hosts` files, but besides that
the router and it's IaC are complete!

For reference, you can find the entire playbook [on
GitHub](https://github.com/jimpudar/my-router).
