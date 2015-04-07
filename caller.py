#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import json
import yaml
import salt.client
import client


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


def generate_roster(filename='/etc/salt/roster'):
    with open(yaml_file, "w+") as yaml_f:
        yaml.safe_dump(data, yaml_f, allow_unicode=True)

def salt_caller():
    client = salt.client.LocalClient()
    ret = client.cmd('*', 'ceph.osd', [])
    print ret


def salt_ssh_caller():
    ssh_client = client.SSHClient()
    ssh_client.cmd("*", "test.ping")
    #ssh_client.cmd('*', 'state.sls', ['some.state'], ssh_timeout, ssh_user=ssh_user, ssh_passwd=ssh_passwd)


if __name__ == '__main__':
    write_pillar()
    #salt_caller()
