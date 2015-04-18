#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import yaml
import jinja2


LIVECLOUD_CONF = '/etc/salt/master.d/livecloud.conf'
LIVECLOUD_ROSTER = '/etc/salt/roster'
SSH_CONF = '/root/.ssh/config'


def prepair_livecloud_conf():
    '''
    params: fsid, public_network, cluster_network host_ips
    '''
    livecloud_template = '''\
auto_accept: False

file_roots:
  base:
      - {{ base_dir }}/salt/

pillar_roots:
  base:
      - {{ base_dir }}/pillar/

'''
    jinja_environment = jinja2.Environment()
    master_conf = get_yaml_from_cfg('master.yml')
    template = jinja_environment.from_string(livecloud_template)
    context = master_conf
    with open(LIVECLOUD_CONF, "wb") as f:
        f.write(template.render(**context))

    roster_template = '''\
{% for ceph in host_ips -%}
{{ ceph['name'] }}:
  host: {{ ceph['ip'] }}
  user: {{ ceph['user'] }}
  passwd: {{ ceph['passwd'] }}
{% endfor -%}
'''
    template = jinja_environment.from_string(roster_template)
    host_ips = master_conf['nodes']
    context.update({'host_ips': host_ips})
    with open(LIVECLOUD_ROSTER, "wb") as f:
        f.write(template.render(**context))

    ssh_template = '''\
{% for ceph in host_ips -%}
host {{ ceph['host'] }}
    StrictHostKeyChecking no
{% endfor -%}
'''
    template = jinja_environment.from_string(ssh_template)
    host_ips = master_conf['nodes']
    context.update({'host_ips': host_ips})
    with open(SSH_CONF, "wb") as f:
        f.write(template.render(**context))

    write_ceph_pillar()


def get_yaml_from_cfg(yaml_file):
    with open(yaml_file) as yaml_f:
        yaml_data = yaml.load(yaml_f)
    return yaml_data


def write_yaml_from_cfg(data, yaml_file):
    with open(yaml_file, "w+") as yaml_f:
        yaml.safe_dump(data, yaml_f, allow_unicode=True)


def write_ceph_pillar(default='ceph.sls'):
    current_path = os.path.dirname(os.path.realpath(__file__))
    dest_file = os.path.join(current_path, 'pillar', default)
    write_yaml_from_cfg(get_yaml_from_cfg('ceph.yml'), dest_file)
    print 'Generate in %s' % dest_file


if __name__ == '__main__':
    prepair_livecloud_conf()
