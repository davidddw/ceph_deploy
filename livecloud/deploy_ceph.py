#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# -*- coding:utf-8 -*-
#
# @author: david_dong

import salt.client
from livecloud import util


LIVECLOUD_CONF = '/etc/salt/master.d'
LIVECLOUD_ROSTER = '/etc/salt/roster'
SSH_CONF = '/root/.ssh'
HOST_CONF = '/etc/hosts'


def parse_from_state(jsondict):
    final_dict = dict()
    for key in jsondict:
        temp_dict = dict()
        final_key = '%s:' % key
        data_dict = jsondict[key]
        new_list = list()
        succ = 0
        fail = 0
        for data_key in data_dict:
            new_obj = dict()
            new_obj['len'] = len(key) + 1
            func_left, myid, myname, func_right = data_key.split('_|-')
            new_obj['id'] = myid
            new_obj['function'] = func_left + '.' + func_right
            new_obj['name'] = myname
            data_value = data_dict[data_key]
            new_obj['number'] = data_value['__run_num__']

            new_obj['result'] = data_value['result']
            if data_value['result']:
                succ += 1
            else:
                fail += 1

            new_obj['comment'] = data_value['comment'].strip()

            if 'changes' in data_value and data_value['changes']:
                new_obj['changes'] = data_value['changes']
            else:
                new_obj['changes'] = ''

            if 'start_time' in data_value:
                new_obj['start'] = data_value['start_time']
            else:
                new_obj['start'] = ''

            if 'duration' in data_value:
                new_obj['duration'] = '%s ms' % data_value['duration']
            else:
                new_obj['duration'] = ''
            new_list.append(new_obj)
            temp_dict['values'] = new_list
            temp_dict['succ'] = succ
            temp_dict['fail'] = fail

        final_dict[final_key] = temp_dict
    return final_dict


def execute_salt_cmd(arg=()):
    local = salt.client.LocalClient()
    result = local.cmd(tgt='*', fun='cmd.run', arg=arg)
    util.pretty_output_cmd(result)


def execute_salt_sls(command, arg=()):
    local = salt.client.LocalClient()
    result = local.cmd(tgt='*', fun=command, arg=arg)
    util.pretty_output_sls(parse_from_state, result)


def execute_salt_modules(command, arg=()):
    local = salt.client.LocalClient()
    result = local.cmd(tgt='*', fun=command, arg=arg)
    print '\n'.join(util.display(result, 0, '', []))


def operate_salt_minion():
    util.output_title('salt highstate')
    execute_salt_sls('state.highstate')
    util.output_title('salt ntp state')
    execute_salt_sls('state.sls', ['ceph.ntp'])
    util.output_title('salt ceph state')
    execute_salt_sls('state.sls', ['ceph.ceph'])
    util.output_title('salt kvm state')
    execute_salt_sls('state.sls', ['ceph.kvm'])
    util.output_title('salt livecloud mon')
    execute_salt_modules('ceph.mon')


def main():
    operate_salt_minion()


if __name__ == '__main__':
    main()
