Title: Adventures in Rolling Your Own Router: Part VI
Date: 2021-01-23
Category: Development
Tags: router, linux, debian, firewall, nftables, ansible
Slug: router-part-6
Author: Jim Pudar
Summary: Automating with Ansible
Status: published

<!-- markdownlint-disable line-length no-trailing-punctuation -->

In my [previous post]({filename}/debian-router-5.md), I set up an `nftables`
firewall. In this post, I'll use [Ansible](https://www.ansible.com) to
automate the configuration steps we have already performed.

# The Purpose of Infrastructure as Code

So far, everything we have done has been manual steps in `vim` and the CLI.
This works fine, but is tedious and error prone. I'm a big proponent of
[Infrastructure as Code
(IaC)](https://en.wikipedia.org/wiki/Infrastructure_as_code). It has countless
advantages in a corporate environment, and I've grown so accustomed to it that
it seems to make sense even for my personal network.

Later, I'll be installing [Pi-hole](https://pi-hole.net/) and after reviewing
the installer, it looks like it does a lot of stuff I might not want. By
defining the router using IaC up to that point, I'll easily be able to get
back to that state if the Pi-hole installer does something I didn't intend to
happen. If I didn't care to have the IaC definition at the end of the process,
I could also accomplish this using VM snapshots. The immediate advantages of
having the IaC definition is that I'll be able to set up the router on real
hardware far more quickly (no downtime = happy family) and if I ever want to
switch to new hardware I'll be able to do so quickly and easily.

# Setting up Ansible

I've only used Ansible a few times, but it was always very straightforward.
The [documentation](https://docs.ansible.com/ansible/latest/index.html), like
most documentation from Red Hat, is fantastic.

I started by adding my virtual `debrouter` to my `/etc/ethers` and
`/etc/hosts` files on my existing DNS server. I also created an
`/etc/ansible/hosts` file on my Mac and added `debrouter` to the file. Then, I
generated a new RSA key pair on my Mac and installed the public key in the
`~/.ssh/authorized_keys` file on `debrouter`. Finally, I set up `NOPASSWD` for
the `sudo` group, and I am now able to use Ansible to ping `debrouter` with
`sudo` privileges:

```text
ansible all -m ping -u jmp --become
debrouter.crbj.io | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```

# Building a Playbook

Now, I can go back in time to last week and start translating the manual steps
I took into an Ansible playbook. I'll start a new file called `playbook.yml`.
I'll also fire up a new Debian 10 VM called debrouter2 we can use for testing
the playbook.

The first step is to determine the MAC address of each interface so I can give
them customized names `extern0` and `intern0`. We can do this using
[facts](https://docs.ansible.com/ansible/latest/user_guide/playbooks_vars_facts.html#vars-and-facts).

Let's assume that on first boot only one of the two interfaces will be
connected to Ethernet and have gotten an IPv4 address via DHCP. This interface
will be our `extern0` interface, and we should be able to find it using the
`default_ipv4` entry in the `ansible_facts` object.

In real life, my router hardware actually has three interfaces, so I may end
up just supplying the interface names manually.

Note that I'm using `set_fact` instead of `vars` because I only want these
filters to be evaluated once.

```text
---
- name: Router Setup
  hosts: debrouter2.crbj.io

  pre_tasks:
  - set_fact:
      ifs: "{{ ansible_facts.interfaces | reject('equalto', 'lo') }}"
  - set_fact:
      external_if: "{{ ansible_facts.default_ipv4.interface }}"
  - set_fact:
      internal_if: "{{ ifs | reject('equalto', external_if) | first }}"
  - set_fact:
      external_if_macaddress: "{{ ansible_facts[external_if].macaddress }}"
  - set_fact:
      internal_if_macaddress: "{{ ansible_facts[internal_if].macaddress }}"

  tasks:
  - name: Print external interface MAC address
    ansible.builtin.debug:
      var: external_if_macaddress
  - name: Print internal interface MAC address
    ansible.builtin.debug:
      var: internal_if_macaddress

```

Now, we need templates for our `.link` files.

```text
% cat templates/link.j2
[Match]
MACAddress={{ macaddress }}

[Link]
Name={{ ifname }}
```

Now we can use the `template` module to automatically place the link files on
the router.

```text
  - name: Set external interface name
    ansible.builtin.template:
      src: templates/link.j2
      dest: /etc/systemd/network/10-extern0.link
      owner: root
      group: root
      mode: '0644'
    vars:
      macaddress: "{{ external_if_macaddress }}"
      ifname: "extern0"
  - name: Set internal interface name
    ansible.builtin.template:
      src: templates/link.j2
      dest: /etc/systemd/network/20-intern0.link
      owner: root
      group: root
      mode: '0644'
    vars:
      macaddress: "{{ internal_if_macaddress }}"
      ifname: "intern0"
```

Next, we add some templates for our `.network` files.

```text
% cat templates/dhcp.network.j2
[Match]
Name={{ ifname }}

[Network]
DHCP=ipv4
% cat templates/static.network.j2
[Match]
Name={{ ifname }}

[Network]
Address={{ address_with_netmask }}
IPForward=true
```

The templates are again fed to the `template` module.

```text
  - name: Set external network configuration
    ansible.builtin.template:
      src: templates/dhcp.network.j2
      dest: /etc/systemd/network/external.network
      owner: root
      group: root
      mode: '0644'
    vars:
      ifname: "extern0"
  - name: Set internal network configuration
    ansible.builtin.template:
      src: templates/static.network.j2
      dest: /etc/systemd/network/internal.network
      owner: root
      group: root
      mode: '0644'
    vars:
      ifname: "intern0"
      address_with_netmask: "192.168.100.1/24"
```

Now, we can use the `systemd` module to disable `networking.service` and
enable `systemd-networkd`. I'm going a step further here and actually masking
`networking.service` so it's not possible to accidentally enable it later.

```text
    - name: Completely disable the default networking.service
      ansible.builtin.systemd:
        name: networking.service
        state: stopped
        enabled: no
        masked: yes
    - name: Enable systemd-networkd.service
      ansible.builtin.systemd:
        name: systemd-networkd.service
        state: started
        enabled: yes
        masked: no
```

We also need to restart the host at this point. Check out the final playbook
[on GitHub](https://github.com/jimpudar/my-router) to see how this is done.

Now we need to install `nftables` and remove `iptables`.

```text
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: yes
    - name: Remove iptables
      ansible.builtin.apt:
        name: iptables
        purge: yes
        state: absent
    - name: Install nftables
      ansible.builtin.apt:
        name: nftables
        state: latest
    - name: Enable nftables.service
      ansible.builtin.systemd:
        name: nftables.service
        state: started
        enabled: yes
        masked: no
```

Finally, we can install the firewall rules using another call to the
`template` module.

```text

    - name: Set up nftables rules
      ansible.builtin.template:
        src: templates/nftables.conf.j2
        dest: /etc/nftables.conf
        owner: root
        group: root
        mode: '0644'
      vars:
        internal_ifname: "intern0"
        external_ifname: "extern0"
        lan_network: "192.168.100.0/24"
```

At this point, we should have a working router. In the [next
post]({filename}/debian-router-7.md), I'll attempt to install Pi-hole without
messing up anything we have done so far.
