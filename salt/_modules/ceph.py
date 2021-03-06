#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# @author: david_dong

import os
import re
import math
import logging
import shlex
import subprocess
import platform
import jinja2

import salt.config
import salt.loader

log = logging.getLogger(__name__)
loglevel = logging.DEBUG
logging.basicConfig(
    level=loglevel,
)

__virtualname__ = 'ceph'


def __virtual__():
    '''
    Rename to ini
    '''
    return __virtualname__


system = platform.system()

if system == "Windows":
    __opts__ = salt.config.minion_config('/etc/salt/minion')
    __salt__ = salt.loader.minion_mods(__opts__)


MON_PATH = '/var/lib/ceph/mon'
OSD_PATH = '/var/lib/ceph/osd'
CEPH_CONF = '/etc/ceph/ceph.conf'
PYAGEXEC_CONF = '/usr/local/livecloud/pyagexec/pyagexec.cfg'
CEPH_CLUSTER = 'ceph'
CEPH_MONMAP = '/var/lib/ceph/tmp/{cluster}_monmap'.format(cluster=CEPH_CLUSTER)


def _get_host():
    return __salt__['config.get']('host')


def _get_fsid():
    return __salt__['pillar.get']('ceph:global:fsid')


def _get_mon_int():
    return __salt__['pillar.get']('ceph:mon:interface')


class CephDiskException(Exception):
    """
    A base exception for ceph-disk to provide custom (ad-hoc) messages that
    will be caught and dealt with when main() is executed
    """
    pass


class ExecutableNotFound(CephDiskException):
    """
    Exception to report on executables not available in PATH
    """
    pass


class Error(Exception):
    """
    Error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


def which(executable):
    """find the location of an executable"""
    if 'PATH' in os.environ:
        envpath = os.environ['PATH']
    else:
        envpath = os.defpath
    PATH = envpath.split(os.pathsep)

    locations = PATH + [
        '/usr/local/bin',
        '/bin',
        '/usr/bin',
        '/usr/local/sbin',
        '/usr/sbin',
        '/sbin',
    ]

    for location in locations:
        executable_path = os.path.join(location, executable)
        if os.path.exists(executable_path):
            return executable_path


def _get_command_executable(command_line):
    """
    Return the full path for an executable, raise if the executable is not
    found. If the executable has already a full path do not perform any checks.
    """
    arguments = shlex.split(command_line)
    if arguments[0].startswith('/'):  # an absolute path
        return arguments
    executable = which(arguments[0])
    if not executable:
        command_msg = 'Could not run command: %s' % ' '.join(arguments)
        executable_msg = '%s not in path.' % arguments[0]
        raise ExecutableNotFound('%s %s' % (executable_msg, command_msg))

    # swap the old executable for the new one
    arguments[0] = executable
    return arguments


def command(command_line, **kwargs):
    """
    This returns the output of the command and the return code of the
    process in a tuple: (output, returncode).
    """
    arguments = _get_command_executable(command_line)
    log.info('Running command: %s' % ' '.join(arguments))
    try:
        process = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            **kwargs)
        out, _ = process.communicate()
        log.info('Execute result: %s', out)
        return out, process.returncode

    except subprocess.CalledProcessError as e:
        raise Error(e)


def pipe_command(command1, command2, **kwargs):
    """
    This returns the output of the command and the return code of the
    process in a tuple: (output, returncode).
    """
    arguments1 = _get_command_executable(command1)
    arguments2 = _get_command_executable(command2)
    log.info('Running command: %s | %s' % (' '.join(arguments1),
                                           ' '.join(arguments2)))
    try:
        process1 = subprocess.Popen(
            arguments1,
            stdout=subprocess.PIPE,
            **kwargs)
        process2 = subprocess.Popen(
            arguments2,
            stdin=process1.stdout,
            stdout=subprocess.PIPE,
            **kwargs)
        process1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        out, _ = process2.communicate()
        log.info('Execute result: %s', out)
        return out, process2.returncode

    except subprocess.CalledProcessError as e:
        raise Error(e)


def cgrep(cmd_string):
    cmd1, cmd2 = cmd_string.split('|')
    ret_code = pipe_command(cmd1, cmd2)[1]
    return True if ret_code == 0 else False


def command_check_call(command_line, **kwargs):
    """
    .. note:: This should be the prefered way of calling
    ``subprocess.check_call`` since it provides the caller with the safety net
    of making sure that executables *will* be found and will error nicely
    otherwise.
    """
    arguments = _get_command_executable(command_line)
    log.info('Running command: %s', ' '.join(arguments))
    ret = subprocess.check_call(arguments, **kwargs)
    log.info('Execute result: %s', ret)
    return ret


def command_check_output(command_line, **kwargs):
    """
    .. note:: This should be the prefered way of calling
    ``subprocess.check_call`` since it provides the caller with the safety net
    of making sure that executables *will* be found and will error nicely
    otherwise.
    """
    arguments = _get_command_executable(command_line)
    log.info('Running command: %s', ' '.join(arguments))
    ret = subprocess.check_output(arguments, **kwargs)
    log.info('Execute result: %s', ret)
    return ret


"""
ceph.conf
"""


def _gen_ceph_conf(**context):
    '''
    params: fsid, public_network, cluster_network host_ips
    '''
    cephconf_template = '''[global]
fsid = {{ fsid }}
pid file = /var/run/ceph/$name.pid
log file = /var/log/ceph/$name.log
cephx cluster require signatures = true
cephx service require signatures = false
public network = {{ public_network }}
cluster network = {{ cluster_network }}
auth cluster required = none
auth service required = none
auth client required = none
max open files = 13107
mon osd down out interval = 600

[mon]
mon initial members = {{ hosts| join(", ")  }}
mon host = {{ ips|join(",") }}
filestore xattr use omap = true
mon data = /var/lib/ceph/mon/$name
mon clock drift allowed = .8
mon pg warn max per osd = 512

[osd]
osd journal size = 20000
osd mkfs type = xfs
osd mkfs options xfs = -f
osd mount options xfs = "rw,noexec,nodev,noatime,inode64,nodiratime,nobarrier"
osd pool default size = 3
osd pool default min size = 1
osd pool default pgnum = {{ total_pgs }}
osd pool default pgpnum = {{ total_pgs }}
osd crush chooseleaf type = 1
osd crush update on start = true
osd op threads = 8
osd client op priority = 63
osd recovery op priority = 4
osd recovery max active = 10
osd disk threads = 4
osd max backfills = 4
osd map cache size = 1024
osd max write size = 512
osd map cache bl size = 128
osd client message size cap = 2147483648
osd deep scrub stride = 131072
osd data=/var/lib/ceph/osd/$cluster-$id
osd journal=/var/lib/ceph/osd/$cluster-$id/journal
filestore xattr use omap = true
filestore min sync interval = 10
filestore max sync interval = 15
filestore queue max ops = 25000
filestore queue max bytes = 10485760
filestore queue committing max ops = 5000
filestore queue committing max bytes = 10485760000
filestore op threads=32
journal max write bytes = 1073714824
journal max write entries = 10000
journal queue max ops = 50000
journal queue max bytes = 10485760000

[client]
rbd cache = true
rbd cache size = 268435456
rbd cache max dirty = 134217728
rbd cache max dirty age = 5

{% for mon in host_ips -%}

[mon.{{ mon['host'] }}]
host = {{ mon['host'] }}
mon addr = {{ mon['ip'] }}:6789

{% endfor -%}
'''
    jinja_environment = jinja2.Environment()
    template = jinja_environment.from_string(cephconf_template)
    host_ips = context['host_ips']
    hosts = [host_ip['host'] for host_ip in host_ips]
    ips = [host_ip['ip'] for host_ip in host_ips]
    context.update({'hosts': hosts, 'ips': ips})
    with open(CEPH_CONF, "wb") as f:
        f.write(template.render(**context))


"""
create mon for each moniter
"""


def _get_mon_hostslist():
    MON_INT = __salt__['pillar.get']('ceph:mon:interface')
    hosts = []
    hostsitems = __salt__['mine.get']('roles:ceph-mon',
                                      'grains.items',
                                      'grain')

    for _, grains in hostsitems.items():
        data = {}
        data.update({'host': grains['host']})
        data.update({'ip': grains['ip_interfaces'][MON_INT][0]})
        hosts.append(data)

    return hosts


def _gen_monmap(host_info_list, fsid=None):
    fsid = fsid or _get_fsid()
    host_string = ''
    for host_info in host_info_list:
        host_fmt = ' --add {host} {ip}:6789 '.format(host=host_info['host'],
                                                     ip=host_info['ip'])
        host_string += host_fmt
    fmt_line = 'monmaptool --cluster={cluster} --create --fsid={fsid} {monmap}'
    command_line = fmt_line.format(cluster=CEPH_CLUSTER,
                                   fsid=fsid,
                                   monmap=CEPH_MONMAP)
    final_line = command_line + host_string + ' --clobber '
    return command_check_output(final_line)


def _ceph_mon_create(host=None):
    host = host or _get_host()
    fmt_line = 'ceph-mon --cluster={cluster} --mkfs -i {host} \
                --monmap {monmap}'
    command_line = fmt_line.format(cluster=CEPH_CLUSTER,
                                   host=host,
                                   monmap=CEPH_MONMAP)
    return command_check_output(command_line)


def _ceph_mon_start(host=None):
    host = host or _get_host()
    fmt_line = 'service ceph start mon.{host}'
    command_line = fmt_line.format(host=host)
    return command(command_line)


def create_mon(host_info_list, fsid=None):
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.create_mon <host_list>
    '''
    fsid = fsid or _get_fsid()
    ret = {'data': {}}
    data = []

    osd_num = __salt__['pillar.get']('ceph:global:total_osd')
    total_pgs = math.pow(2, (math.ceil(math.log(
                int(osd_num)*100/3)/math.log(2))))

    # gen /etc/ceph/ceph.conf
    _gen_ceph_conf(
        fsid=fsid,
        public_network=__salt__['pillar.get']('ceph:global:cluster_network'),
        cluster_network=__salt__['pillar.get']('ceph:global:public_network'),
        total_pgs=int(total_pgs),
        host_ips=host_info_list
    )

    # gen_mon_map
    # Test monmap if exists
    if not __salt__['file.file_exists'](CEPH_MONMAP):
        data.append({'gen_monmap': _gen_monmap(host_info_list, fsid)})

    # populate_mon
    mon_host = os.path.join(MON_PATH, 'mon.{host}'.format(host=_get_host()))
    # Test mon_host if exists
    if not __salt__['file.directory_exists'](mon_host):
        data.append({'gen_monmap': _ceph_mon_create(_get_host())})

    # start_mon
    ceph_host = os.path.join(
        MON_PATH,
        '{cluster}-{host}'.format(cluster=CEPH_CLUSTER, host=_get_host())
    )
    __salt__['file.mkdir'](ceph_host)
    __salt__['file.touch'](os.path.join(ceph_host, 'done'))
    __salt__['file.touch'](os.path.join(ceph_host, 'sysvinit'))

    # start_mon
    if __salt__['file.file_exists'](os.path.join(ceph_host, 'done')):
        data.append({'service': _ceph_mon_start(_get_host())})

    ret['data'] = data
    ret['comment'] = 'Create ceph mon node'
    ret['result'] = True
    return ret


def mon():
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.mon
    '''
    return create_mon(_get_mon_hostslist(), _get_fsid())


def add_mon():
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.add_mon
    '''
    return create_mon(_get_mon_hostslist(), _get_fsid())


"""
create osd for each osd
"""


def _get_osd_hostslist():
    devices = []
    hostsitems = __salt__['mine.get']('roles:ceph-osd',
                                      'grains.items',
                                      'grain')

    for _, grains in hostsitems.items():
        data = {}
        data.update({'host': grains['host']})
        data.update({'ip': __salt__['pillar.get'](
            'nodes:' + grains['host'] + ':devs')})
        devices.append(data)

    return devices


def _osd_crush_map(osd_id, host=None):
    # ceph_osd_crush
    host = host or _get_host()
    fmt_line = 'ceph osd crush add-bucket {host} host'
    command_check_output(fmt_line.format(host=host))
    fmt_line = 'ceph osd crush move {host} root=default'
    command_check_output(fmt_line.format(host=host))
    fmt_line = 'ceph osd crush add osd.{osd_id} 1.0 host={host}'
    command_check_output(fmt_line.format(osd_id=osd_id, host=host))


def _partiton_exist(**kwargs):
    '''
    @params: dev, value
    '''
    fmt_line = 'sgdisk --print /dev/{dev} | grep {value}'
    return cgrep(fmt_line.format(**kwargs))


def _make_gpt_label(**kwargs):
    '''
    @params: dev
    '''
    fmt_line = 'parted -s /dev/{dev} print | grep gpt'
    if not cgrep(fmt_line.format(**kwargs)):
        fmt_line = 'parted -s /dev/{dev} mklabel gpt'
        return command_check_output(fmt_line.format(**kwargs))
    else:
        return None


def _parted_dev(**kwargs):
    '''
    @params: dev, osd_uuid
    '''
    import uuid
    ptype_tobe = '89c57f98-2fe5-4dc0-89c1-f3ad0ceff2be'
    osd_uuid = uuid.uuid4()
    kwargs.update({'ptype_tobe': ptype_tobe})

    fmt_line = 'sgdisk --largest-new=1 --change-name="1:ceph data" \
            --partition-guid=1:{osd_uuid} \
            --typecode=1:{ptype_tobe} -- /dev/{dev}'
    kwargs.update({'osd_uuid': osd_uuid})
    _make_gpt_label(**kwargs)
    return command_check_output(fmt_line.format(**kwargs))


def _parted_journal(**kwargs):
    '''
    @params: journal_dev, count, per_size
    '''
    unit = kwargs['per_size'][-1]
    size = int(kwargs['per_size'][:-1])
    final_string = 'sgdisk '

    fmt_line = '-n {partnum}:0:+{size}{unit} -c "{partnum}:ceph journal" '
    for i in range(kwargs['count']):
        final_string += fmt_line.format(partnum=i+1, unit=unit, size=size)
    final_string += '-p /dev/{journal}'.format(journal=kwargs['journal_dev'])
    return command_check_output(final_string)


def journal():
    ret = {'data': {}}
    data = []
    journals = __salt__['pillar.get']('nodes:' + _get_host() + ':journal')
    for journal in journals:
        part_regex = 'nodes:{host}:journal:{journal}:partition'
        part_size = __salt__['pillar.get'](
            part_regex.format(host=_get_host(),
                              journal=journal)
        )
        if not _partiton_exist(dev=journal, value='journal'):
            data.append({'parted': _parted_journal(
                journal_dev=journal, count=part_size['count'],
                per_size=part_size['per_size'])
            })
    ret['data'] = data
    ret['comment'] = 'Create journal partition'
    ret['result'] = True
    return ret


def _mkfs_dev(**kwargs):
    '''
    @params: dev
    '''
    fmt_line = 'mkfs -t xfs -f /dev/{dev}1'
    return command_check_output(fmt_line.format(**kwargs))


def _dev_to_uuid(dev):
    blkid_info = __salt__['disk.blkid']()
    device_uuid = blkid_info.get(dev, {}).get('UUID')
    return 'UUID=%s' % (device_uuid)


def _mount_dev(**kwargs):
    '''
    @params: osd_mount_point, osd_dev_uuid
    '''
    if not os.path.exists(kwargs['osd_mount_point']):
        __salt__['file.mkdir'](kwargs['osd_mount_point'])
    __salt__['mount.mount'](kwargs['osd_mount_point'], kwargs['osd_dev_uuid'],
                            fstype='xfs')
    return __salt__['mount.set_fstab'](kwargs['osd_mount_point'],
                                       kwargs['osd_dev_uuid'], 'xfs')


def _replace_journal(**kwargs):
    '''
    @params: osd_node, osd_id, journal_dev, journal_path
    '''
    if __salt__['file.file_exists'](kwargs['journal_path']):
        # flush_journal
        fmt_line = 'ceph-osd -i {osd_id} --flush-journal'
        command_check_output(fmt_line.format(osd_id=kwargs['osd_id']))
        # rm_journal
        __salt__['file.remove'](kwargs['journal_path'])

        # link_journal
        __salt__['file.symlink'](
            '/dev/{journal}'.format(journal=kwargs['journal_dev']),
            kwargs['journal_path']
        )
        # recreate_journal
        fmt_line = 'ceph-osd -i {osd_id} --mkjournal'
        command_check_output(fmt_line.format(osd_id=kwargs['osd_id']))


def _ceph_osd_create(osd_id, osd):
    '''
    @params: osd_node, osd_id, journal_dev, journal_path
    '''
    fmt_line = 'ceph-osd -i {osd_id} --osd-data={osd} --mkfs'
    return command_check_output(
        fmt_line.format(osd_id=osd_id, osd=osd))


def _update_ini(osd_id, curr_host):
    section = 'osd.{osd_id}'.format(osd_id=osd_id)
    value = {'host': curr_host}
    __salt__['ini.set_option'](CEPH_CONF, {section: value})


def _ceph_osd_start(osd_id=None):
    if osd_id is None:
        fmt_line = 'service ceph start osd'
    else:
        fmt_line = 'service ceph start osd.{osd_id}'
    command_line = fmt_line.format(osd_id=osd_id)
    return command(command_line)


def _ceph_autostart():
    return command('chkconfig ceph on')


def _is_mount(dev_uuid):
    fstablists = __salt__['mount.fstab']()
    ret = False
    for _, entry in fstablists.items():
        if entry['device'] == dev_uuid:
            ret = True
            break
    return ret


def _get_id_from_dev(osd_dev_uuid):
    fstablists = __salt__['mount.fstab']()
    osd_mount_point = ''
    for key, entry in fstablists.items():
        if entry['device'] == osd_dev_uuid:
            osd_mount_point = key
            break

    ret = re.findall(r'(\d+)', osd_mount_point)
    return int(ret[0]) if ret else -1


def create_osd(dev, journal_dev=None):
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.create_osd <dev> <journal_dev>
    '''
    def __get_osd_mount_point(osd_id):
        return os.path.join(OSD_PATH, 'ceph-{osd_id}'.format(osd_id=osd_id))

    ret = {'data': {}}
    data = []
    # prepare_disk

    if not _partiton_exist(dev=dev, value='ceph'):
        data.append({'parted': _parted_dev(dev=dev)})
        data.append({'parted': _mkfs_dev(dev=dev)})
    else:
        data.append({'parted': 'exist'})

    # format_disk
    # fmt_line = 'parted -s /dev/{dev} print | grep xfs'
    # if not cgrep(fmt_line.format(dev=dev)):
    #    data.append({'parted': _mkfs_dev(dev=dev)})
    # else:
    #    data.append({'parted': 'exist'})

    # mount_osd
    osd_dev = '/dev/{dev}1'.format(dev=dev)
    osd_dev_uuid = _dev_to_uuid(osd_dev)
    if not _is_mount(osd_dev_uuid):
        fmt_line = 'ceph osd create'
        osd_id = command_check_output(fmt_line).strip()
        data.append({'osd_id': osd_id})
        data.append({'mounted': _mount_dev(
            osd_dev_uuid=osd_dev_uuid,
            osd_mount_point=__get_osd_mount_point(osd_id))
        })
    else:
        osd_id = _get_id_from_dev(osd_dev_uuid)
        data.append({'osd_id': osd_id})
        data.append({'mounted': 'already'})

    # create_osd
    osd_mount_point = __get_osd_mount_point(osd_id)
    ready_path = os.path.join(osd_mount_point, 'ready')
    if not __salt__['file.file_exists'](ready_path):
        data.append({'create': _ceph_osd_create(osd_id, osd_mount_point)})
    else:
        data.append({'create': 'already'})

    # change_journal
    journal_path = os.path.join(osd_mount_point, 'journal')
    if journal_dev and not __salt__['file.is_link'](journal_path):
        _replace_journal(osd_node=osd_mount_point,
                         osd_id=osd_id,
                         journal_dev=journal_dev,
                         journal_path=journal_path)

    if __salt__['file.file_exists'](journal_path):
        # ceph_osd_crush
        _osd_crush_map(osd_id, _get_host())

    # _update_ini(osd_id, _get_host())
    __salt__['file.touch'](os.path.join(osd_mount_point, 'sysvinit'))

    data.append({'service': _ceph_osd_start(osd_id)})
    data.append({'autostart': _ceph_autostart()})
    ret['data']['osd.{osd_id}'.format(osd_id=osd_id)] = data
    ret['comment'] = 'Create ceph osd node'
    ret['result'] = True
    return ret


def osd():
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.osd
    '''
    ret = []
    devs = __salt__['pillar.get']('nodes:' + _get_host() + ':devs')
    for dev in devs:
        fmt_line = 'nodes:{host}:devs:{dev}:journal'
        journal = __salt__['pillar.get'](
            fmt_line.format(host=_get_host(), dev=dev))
        ret.append(create_osd(dev, journal))
    return ret


def generate_udev_rules(disk, attr1, attr2):
    rules_fmt = '{subsystem}, {action}, {kernel}, {attr1}, {attr2}\n'
    return rules_fmt.format(
                subsystem='SUBSYSTEM=="block"',
                action='ACTION=="add|change"',
                kernel='KERNEL=="' + disk + '"',
                attr1='ATTR{queue/rotational}="' + str(attr1) + '"',
                attr2='ATTR{queue/scheduler}="' + attr2 + '"',)


def udev_rules():
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.udev_rules
    '''
    ret = []
    ssd_list = __salt__['pillar.get']('nodes:' + _get_host() + ':ssd_list')
    hdd_list = list()
    devs = __salt__['pillar.get']('nodes:' + _get_host() + ':devs')
    for dev in devs:
        if dev not in ssd_list:
            hdd_list.append(dev)

    rules = ""
    for hdd in hdd_list:
        rules += generate_udev_rules(hdd, 1, 'deadline')
    for ssd in ssd_list:
        rules += generate_udev_rules(ssd, 0, 'noop')

    __salt__['file.touch']('/etc/udev/rules.d/99-ssd.rules')
    __salt__['file.append']('/etc/udev/rules.d/99-ssd.rules', rules)
    ret['comment'] = 'udevadm control --reload-rules'
    command_check_output('udevadm control --reload-rules')
    command_check_output('udevadm trigger')
    ret['result'] = True
    return ret


def uuid():
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.uuid
    '''
    ret = []
    ret.append(_dev_to_uuid('/dev/sdb1'))
    return ret


def pool():
    '''
    CLI Example:
    .. code-block:: bash
        salt '*' ceph.pool
    '''
    ret = {'data': {}}
    data = []
    fmt_line = 'ceph osd pool create {name} {pg_num} {pgp_num}'
    pools = __salt__['pillar.get']('ceph:pools')
    osd_num = __salt__['pillar.get']('ceph:global:total_osd')
    total_pgs = math.pow(2, (math.ceil(math.log(
                        int(osd_num)*100/3)/math.log(2))))
    for pool in pools:
        pool.update({'pg_num': int(total_pgs)})
        pool.update({'pgp_num': int(total_pgs)})
        data.append(command_check_output(fmt_line.format(**pool)))
    no_out_cmd = 'ceph osd set noout'
    data.append(command_check_output(no_out_cmd))
    ret['data'] = data
    ret['comment'] = 'Create ceph pool'
    ret['result'] = True
    return ret


if __name__ == '__main__':
    pass
