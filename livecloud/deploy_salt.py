# -*- coding:utf-8 -*-
#
# @author: david_dong

import os
import re
import yaml
import jinja2
from livecloud import util

from salt.client.ssh.client import SSHClient


LIVECLOUD_CONF = '/etc/salt/master.d'
LIVECLOUD_ROSTER = '/etc/salt/roster'
SSH_CONF = '/root/.ssh'
HOST_CONF = '/etc/hosts'


def get_root_dir():
    current_path = os.path.dirname(os.path.realpath(__file__))
    pattern = re.compile(r'\livecloud\S*')
    found = re.findall(pattern, current_path)
    root_dir = ''

    if found is not None:
        root_dir = re.sub(pattern, '', current_path)
    return root_dir


def render_template(tempate_name, dest_file, **context):
    template_path = os.path.join(get_root_dir(), 'templates')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    template = env.get_template(tempate_name)
    with open(dest_file, "wb") as f:
        f.write(template.render(**context))


def write_yaml_from_cfg(data, yaml_file):
    with open(yaml_file, "w+") as yaml_f:
        yaml.safe_dump(data, yaml_f, allow_unicode=True)


def get_yaml_from_cfg(yaml_file):
    yaml_file = os.path.join(get_root_dir(), 'conf', yaml_file)
    with open(yaml_file) as yaml_f:
        yaml_data = yaml.load(yaml_f)
    return yaml_data


def write_ceph_pillar(default='ceph.sls'):
    dest_file = os.path.join(get_root_dir(), 'pillar', default)
    write_yaml_from_cfg(get_yaml_from_cfg('ceph.yml'), dest_file)
    util.log_screen('Generate in %s\n' % dest_file)


def parse_from_dict(jsondict):
    final_dict = dict()
    for key in jsondict:
        temp_dict = dict()
        final_key = '%s:' % key
        if 'return' in jsondict[key]:
            return_dict = jsondict[key]['return']
            new_list = list()
            succ = 0
            fail = 0
            for return_key in return_dict:
                new_obj = dict()
                new_obj['len'] = len(key) + 1
                func_left, myid, myname, func_right = return_key.split('_|-')
                new_obj['id'] = myid
                new_obj['function'] = func_left + '.' + func_right
                new_obj['name'] = myname
                return_value = return_dict[return_key]
                new_obj['number'] = return_value['__run_num__']

                new_obj['result'] = return_value['result']
                if return_value['result']:
                    succ += 1
                else:
                    fail += 1

                new_obj['comment'] = return_value['comment'].strip()

                if 'changes' in return_value and return_value['changes']:
                    new_obj['changes'] = return_value['changes']
                else:
                    new_obj['changes'] = ''

                if 'start_time' in return_value:
                    new_obj['start'] = return_value['start_time']
                else:
                    new_obj['start'] = ''

                if 'duration' in return_value:
                    new_obj['duration'] = '%s ms' % return_value['duration']
                else:
                    new_obj['duration'] = ''
                new_list.append(new_obj)
            temp_dict['values'] = new_list
            temp_dict['succ'] = succ
            temp_dict['fail'] = fail

        final_dict[final_key] = temp_dict
    return final_dict


def prepair_livecloud_conf():
    '''
    params: fsid, public_network, cluster_network host_ips
    '''
    if not os.path.exists(LIVECLOUD_CONF):
        os.mkdir(LIVECLOUD_CONF)
    livecloud_conf = os.path.join(LIVECLOUD_CONF, 'livecloud.conf')
    if not os.path.exists(SSH_CONF):
        os.mkdir(SSH_CONF)
    ssh_conf = os.path.join(SSH_CONF, 'config')
    master_conf = get_yaml_from_cfg('master.yml')
    context = master_conf
    context.update({'base_dir': get_root_dir()})
    render_template('livecloud.tmpl', livecloud_conf, **context)
    util.log_screen('write livecloud.conf successful')
    host_ips = master_conf['nodes']
    context.update({'host_ips': host_ips})
    render_template('roster.tmpl', LIVECLOUD_ROSTER, **context)
    util.log_screen('write roster successful')
    host_ips = master_conf['nodes']
    context.update({'host_ips': host_ips})
    render_template('ssh.tmpl', ssh_conf, **context)
    util.log_screen('write ssh.conf successful')
    host_ips = master_conf['nodes']
    context.update({'host_ips': host_ips})
    render_template('hosts.tmpl', HOST_CONF, **context)
    util.log_screen('write hosts successful')
    write_ceph_pillar()


def execute_salt_ssh(arg=()):
    client = SSHClient()
    result = client.cmd(tgt='*', fun='cmd.run', arg=arg)
    util.pretty_output_ssh(result)


def execute_salt_sls(command, arg=()):
    client = SSHClient()
    result = client.cmd(tgt='*', fun=command, arg=arg)
    util.pretty_output_sls(parse_from_dict, result)


def deploy_salt_minion(nic):
    ipaddr = util.get_local_ipaddr(nic)[0]
    hostname = util.resolve_ip()
    cmd = 'echo "%s %s" >> /etc/hosts;' % (ipaddr, hostname)
    cmd += 'echo "[yum]" > /etc/yum.repos.d/yum.repo;'
    cmd += 'echo "name=YUM" >> /etc/yum.repos.d/yum.repo;'
    cmd += 'echo "baseurl=http://%s" >> /etc/yum.repos.d/yum.repo;' % (ipaddr)
    cmd += 'echo "enabled=1" >> /etc/yum.repos.d/yum.repo;'
    cmd += 'echo "gpgcheck=0" >> /etc/yum.repos.d/yum.repo;'
    cmd += 'yum --disablerepo=\* --enablerepo=yum install -y yum-utils;'
    execute_salt_ssh(arg=[cmd])
    execute_salt_sls('state.sls', ['ceph.minion'])


def main():
    util.output_title('prepair livecloud env')
    prepair_livecloud_conf()
    util.output_title('delpoy salt minion')
    deploy_salt_minion('eth0')


if __name__ == '__main__':
    main()
