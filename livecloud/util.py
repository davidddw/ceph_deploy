# -*- coding:utf-8 -*-
#
# @author: david_dong

import socket
import netifaces

from termcolor import colored
from numbers import Number
from salt.ext.six import string_types


def resolve_ip():
    """
    Resolve the IP address and handle errors...
    """
    try:
        return socket.gethostname()
    except:
        return None


def get_local_ipaddr(nic):
    ipaddr = '127.0.0.1'
    ipmask = '255.0.0.0'
    all_nics = netifaces.interfaces()
    if nic in all_nics:
        nic_interface = netifaces.ifaddresses(nic)
        ipv4 = nic_interface[netifaces.AF_INET]
        if len(ipv4) > 0:
            ipaddr = ipv4[0]['addr']
            ipmask = ipv4[0]['netmask']
    return ipaddr, ipmask


def log_screen(text):
    print colored('==> %s' % text, 'cyan', attrs=['dark'])


def colored_cyan(text):
    return colored(text, 'cyan', attrs=['dark'])


def colored_green(text):
    return colored(text, 'green', attrs=['dark'])


def colored_green_bold(text):
    return colored(text, 'green', attrs=['bold'])


def colored_red(text):
    return colored(text, 'red', attrs=['dark'])


def colored_yellow(text):
    return colored(text, 'yellow', attrs=['dark'])


def colored_yellow_bold(text):
    return colored(text, 'yellow', attrs=['bold'])


def output_title(title):
    print colored(title, 'yellow', attrs=['bold', 'dark'])


def ustring(indent, raw_string, prefix='', suffix=''):
    indent *= ' '
    return '{0}{1}{2}{3}'.format(indent, prefix, raw_string, suffix)


def display(data, indent, prefix, out):
    if data is None or data is True or data is False:
        out.append(colored_yellow_bold(ustring(indent, data, prefix)))
    elif isinstance(data, Number):
        out.append(colored_yellow_bold(ustring(indent, data, prefix)))
    elif isinstance(data, string_types):
        for line in data.splitlines():
            out.append(colored_green(ustring(indent, line, prefix)))
    elif isinstance(data, (list, tuple)):
        for ind in data:
            if isinstance(ind, (list, tuple, dict)):
                out.append(colored_green(ustring(indent, '|_')))
                prefix = '' if isinstance(ind, dict) else '- '
                display(ind, indent + 2, prefix, out)
            else:
                display(ind, indent, '- ', out)
    elif isinstance(data, dict):
        if indent:
            out.append(colored_cyan(ustring(indent, '----------', prefix)))
        for key in sorted(data):
            val = data[key]
            out.append(colored_cyan(ustring(indent, key, suffix=':',
                                            prefix=prefix)))
            display(val, indent + 4, '', out)
    return out


def pretty_output_cmd(data):
    output_list = list()
    for key in data:
        output_list.append(colored_cyan(ustring(0, key, suffix=':')))
        output_list.append(colored_green(ustring(4, data[key], suffix=':')))
    print('\n'.join(output_list))


def pretty_output_ssh(data):
    output_list = list()
    for key in data:
        output_list.append(colored_cyan(ustring(0, key, suffix=':')))
        if len(data[key]) > 0:
            output_list.append(colored_cyan(ustring(4, '-' * 10)))
            output_list.append(colored_cyan(ustring(4, 'retcode:')))
            if 'retcode' in data[key]:
                output_text = ustring(8, data[key]['retcode'])
                output_list.append(colored_yellow(output_text))
            output_list.append(colored_cyan(ustring(4, 'return')))
            if 'return' in data[key]:
                output_text = ustring(8, data[key]['return'])
                new_output = ('\n' + ' ' * 8).join(output_text.split('\n'))
                output_list.append(colored_green(new_output))
            output_list.append(colored_cyan(ustring(4, 'stderr')))
            if 'stderr' in data[key]:
                output_text = ustring(8, data[key]['stderr'])
                new_output = ('\n' + ' ' * 8).join(output_text.split('\n'))
                output_list.append(colored_red(new_output))
            output_list.append(colored_cyan(ustring(4, 'stdout')))
            if 'stdout' in data[key]:
                output_text = ustring(8, data[key]['stdout'])
                new_output = ('\n' + ' ' * 8).join(output_text.split('\n'))
                output_list.append(colored_green(new_output))

    print('\n'.join(output_list))


def output_changes(changes):
    output_list = list()
    output_list.append('')
    if len(changes) > 0:
        output_list.append(colored_cyan(ustring(0, '-' * 10)))
    for key in changes:
        output_list.append(colored_cyan(key) + colored_green_bold(':'))
        change = changes[key]
        if isinstance(change, dict):
            if len(change) > 0:
                output_list.append(colored_cyan(ustring(4, '-' * 10)))
            for subkey in change:
                output_list.append(' ' * 4 + colored_cyan(subkey) +
                                   colored_green_bold(':'))
                if change[subkey] != '':
                    output_list.append(colored_green(ustring(8,
                                                             change[subkey])))
        elif isinstance(change, str):
            output_list.extend([colored_green(ustring(4, i))
                                for i in change.split('\n')])
        else:
            output_list.append(colored_yellow_bold(ustring(4, change)))
    return ('\n' + ' ' * 14).join(output_list)


def printable_summary(succ_num, fail_num):
    output_list = list()
    output_list.append(colored_cyan('\nSummary'))
    maxlen = max(len(str(succ_num)), len(str(fail_num)))
    succ = '{0:<10} {1:>{width}}'.format('Succeeded:', succ_num, width=maxlen)
    fail = '{0:<10} {1:>{width}}'.format('Failed:', fail_num, width=maxlen)
    sep_line = '-' * (maxlen + 11)
    output_list.append(colored_cyan(sep_line))
    output_list.append(colored_green(succ))
    if fail_num > 0:
        output_list.append(colored_red(fail))
    else:
        output_list.append(colored_cyan(fail))
    output_list.append(colored_cyan(sep_line))
    total = 'Total states run:     {}'.format(succ_num + fail_num)
    output_list.append(colored_cyan(total))
    return '\n'.join(output_list)


def pretty_output_sls(parse_from_dict, data):
    final_data = parse_from_dict(data)
    output_list = list()
    for key in final_data:
        if final_data[key]['fail'] == 0:
            output_list.append(colored_green(key))
        else:
            output_list.append(colored_red(key))

        value_list = final_data[key]['values']
        values = sorted(value_list, key=lambda x: x['number'])
        for obj in values:
            output_list.append(printable_obj(obj, obj["result"]))
        output_list.append(printable_summary(final_data[key]['succ'],
                                             final_data[key]['fail']))
    print('\n'.join(output_list))


def printable_obj(obj, result=True):
    output_list = list()
    output_list.append('-' * obj["len"])
    output_list.append('{:>12}: {}'.format("ID", obj["id"]))
    output_list.append('{:>12}: {}'.format("Function", obj["function"]))
    output_list.append('{:>12}: {}'.format("Name", obj["name"]))
    output_list.append('{:>12}: {}'.format("Result", obj["result"]))
    new_comment = ('\n' + ' ' * 14).join(obj["comment"].split('\n'))
    output_list.append('{:>12}: {}'.format("Comment", new_comment))
    output_list.append('{:>12}: {}'.format("Started", obj["start"]))
    output_list.append('{:>12}: {}'.format("Duration", obj["duration"]))
    if obj["changes"]:
        changes = output_changes(obj["changes"])
    else:
        changes = ''
    output_list.append('{:>12}: {}'.format("Changes", changes))
    buf = '\n'.join(output_list)
    if result:
        return colored_green(buf)
    else:
        return colored_red(buf)
