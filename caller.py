#!/usr/bin/env python
# -*- coding:utf-8 -*-

import salt.client


def ceph_install():
    client = salt.client.LocalClient()
    ret = client.cmd('*', 'saltutil.sync_all', [])
    print ret
    ret = client.cmd('*', 'ceph.journal', [])
    print ret
    ret = client.cmd('*', 'ceph.mon', [])
    print ret
    ret = client.cmd('*', 'ceph.osd', [])
    print ret
    ret = client.cmd('*', 'ceph.pool', [])
    print ret


def kvm_install():
    client = salt.client.LocalClient()
    ret = client.cmd('*', 'kvm.pool', [])
    print ret


if __name__ == '__main__':
    ceph_install()
