#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import json
import yaml
import salt.client
import client
import ConfigParser


def get_json_from_cfg(json_file):
    with open(json_file) as json_f:
        json_data = json.load(json_f)
    return json_data


def write_yaml_from_cfg(data, yaml_file):
    with open(yaml_file, "w+") as yaml_f:
        yaml.safe_dump(data, yaml_f, allow_unicode=True)


def write_pillar(default='ceph.sls'):
    current_path = os.path.dirname(os.path.realpath(__file__))
    print current_path
    dest_file = os.path.join(current_path, 'pillar', default)
    write_yaml_from_cfg(get_json_from_cfg('ceph.json'), dest_file)


def generate_roster(hostlist, filename='/etc/salt/roster'):
    config = ConfigParser.RawConfigParser()

    for host in hostlist:
        config.add_section(host['name'])
        config.set(host['name'], 'host', host['ip'])
        config.set(host['name'], 'user', host['user'])
        config.set(host['name'], 'passwd', host['passwd'])

    with open(filename, 'wb') as configfile:
        config.write(configfile)


def salt_caller():
    client = salt.client.LocalClient()
    ret = client.cmd('*', 'ceph.mon', [])
    print ret
    ret = client.cmd('*', 'ceph.osd', [])
    print ret
    ret = client.cmd('*', 'ceph.pool', [])
    print ret
    ret = client.cmd('*', 'kvm.pool', [])
    print ret


if __name__ == '__main__':
    write_pillar()
    salt_caller()
