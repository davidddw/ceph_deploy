#!/usr/bin/env python

import os
import subprocess
import time
import logging
import ConfigParser


log = logging.getLogger(__name__)
loglevel = logging.DEBUG
logging.basicConfig(
    level=loglevel,
)


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


def create_done_path(done_path):
    """create a done file to avoid re-doing the mon deployment"""
    with file(done_path, 'w'):
        pass


def create_mon_path(path):
    """create the mon path if it does not exist"""
    if not os.path.exists(path):
        os.makedirs(path)


def create_init_path(init_path):
    """create the init path if it does not exist"""
    if not os.path.exists(init_path):
        with file(init_path, 'w'):
            pass


def append_to_file(file_path, contents):
    """append contents to file"""
    with open(file_path, 'a') as f:
        f.write(contents)


def readline(path):
    with open(path) as _file:
        return _file.readline().strip('\n')


def path_exists(path):
    return os.path.exists(path)


def file_exists(path):
    return os.path.isfile(path)


def get_realpath(path):
    return os.path.realpath(path)


def listdir(path):
    return os.listdir(path)


def makedir(path, ignored=None):
    ignored = ignored or []
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno in ignored:
            pass
        else:
            # re-raise the original exception
            raise


def unlink(_file):
    os.unlink(_file)


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


def object_grep(term, file_object):
    for line in file_object.readlines():
        if term in line:
            return True
    return False


def grep(term, file_path):
    # A small grep-like function that will search for a word in a file and
    # return True if it does and False if it does not.

    # return ``False`` if the file does not exist.
    if not os.path.isfile(file_path):
        return False

    with open(file_path) as _file:
        return object_grep(term, _file)


def cgrep(pattern, cmd_string):
    import re

    for line in command_check_output(cmd_string):
        if re.search(pattern, line):
            return True
    return False


def write_conf(filename, section, option, value):
    conf = ConfigParser.ConfigParser()
    conf.read(filename)
    sections = conf.sections()
    if section not in sections:
        conf.add_section(section)
    conf.set(section, option, value)
    conf.write(open(filename, "w"))


def _get_command_executable(arguments):
    """
    Return the full path for an executable, raise if the executable is not
    found. If the executable has already a full path do not perform any checks.
    """
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


def command(arguments, **kwargs):
    """
    This returns the output of the command and the return code of the
    process in a tuple: (output, returncode).
    """
    arguments = _get_command_executable(arguments)
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


def command_check_call(arguments, **kwargs):
    """
    .. note:: This should be the prefered way of calling
    ``subprocess.check_call`` since it provides the caller with the safety net
    of making sure that executables *will* be found and will error nicely
    otherwise.
    """
    arguments = _get_command_executable(arguments)
    log.info('Running command: %s', ' '.join(arguments))
    ret = subprocess.check_call(arguments, **kwargs)
    log.info('Execute result: %s', ret)
    return ret


def command_check_output(arguments, **kwargs):
    """
    .. note:: This should be the prefered way of calling
    ``subprocess.check_call`` since it provides the caller with the safety net
    of making sure that executables *will* be found and will error nicely
    otherwise.
    """
    arguments = _get_command_executable(arguments)
    log.info('Running command: %s', ' '.join(arguments))
    ret = subprocess.check_output(arguments, **kwargs)
    log.info('Execute result: %s', ret)
    return ret


mon_path = '/var/lib/ceph/mon'
osd_path = '/var/lib/ceph/osd'
ceph_conf = '/etc/ceph/ceph.conf'


def create_mon(cluster, fsid, monmap, curr_host, hosts_infos):

    ret = {'name': 'create_mon',
           'result': False,
           'comment': '',
           'changes': {},
           'data': {}}  # Data field for monitoring state
    # gen_mon_map
    if not path_exists(monmap):
        cmd_string = [
            'monmaptool',
            '--cluster={cluster}'.format(cluster=cluster),
            '--create',
            '--fsid={fsid}'.format(fsid=fsid),
            '--clobber',
        ]
        for host_info in hosts_infos:
            cmd_temp = [
                '--add',
                '{host}'.format(host=host_info['host']),
                '{ip}:6789'.format(ip=host_info['ip']),
            ]
            cmd_string.extend(cmd_temp)
        cmd_string.append(monmap)
        command_check_output(cmd_string)

    # populate_mon
    mon_host = os.path.join(mon_path, 'mon.{host}'.format(host=curr_host))
    if not path_exists(mon_host):
        cmd_string = [
            'ceph-mon',
            '--cluster={cluster}'.format(cluster=cluster),
            '--mkfs',
            '-i',
            '{host}'.format(host=curr_host),
            '--monmap',
            monmap,
        ]
        command_check_output(cmd_string)

    # start_mon
    ceph_host = os.path.join(
        mon_path,
        '{cluster}-{host}'.format(cluster=cluster, host=curr_host)
    )
    create_mon_path(ceph_host)
    create_done_path(os.path.join(ceph_host, 'done'))

    # start_mon
    if file_exists(os.path.join(ceph_host, 'done')):
        start_mon = [
            'service',
            'ceph',
            'start',
            'mon.{host}'.format(host=curr_host),
        ]
        ret['data'].update({'service': command(start_mon)})

    ret['comment'] = 'Create ceph mon node'
    ret['result'] = True
    return ret


def create_osd(osd_id, dev, uuid, journal_dev, curr_host):
    ret = {'name': 'create_osd',
           'result': False,
           'comment': '',
           'changes': {},
           'data': {}}  # Data field for monitoring state
    # prepare_disk
    args = ['parted',
            '--script',
            '/dev/{dev}'.format(dev=dev),
            'print']
    if not cgrep('ceph', args):
        args = [
            'parted',
            '-s',
            '/dev/{dev}'.format(dev=dev),
            'mklabel',
            'gpt',
            '--',
            'mkpart',
            '"ceph"',
            'xfs',
            '0',
            '-1',
        ]
        command_check_output(args)

    # format_disk
    if not cgrep('{dev}1'.format(dev=dev), ['ls', r'/dev/']):
        args = [
            'mkfs',
            '-t',
            'xfs',
            '-f',
            '/dev/{dev}1'.format(dev=dev),
        ]
        command_check_output(args)

    # mount_osd
    pattern = 'ceph-{osd_id}'.format(osd_id=osd_id)
    if not cgrep(pattern, ['ls', osd_path]):
        osd_mount_point = os.path.join(osd_path, pattern)
        makedir(osd_mount_point)
        args = [
            'mount',
            '/dev/{dev}1'.format(dev=dev),
            osd_mount_point,
        ]
        command_check_output(args)

    # create_osd
    osd_node = os.path.join(osd_path, 'ceph-{osd_id}'.format(osd_id=osd_id))
    if not file_exists(os.path.join(osd_node, 'ready')):
        args = [
            'ceph-osd',
            '-i',
            '{osd_id}'.format(osd_id=osd_id),
            '--osd-data={osd}'.format(osd=os.path.join(osd_path, osd_node)),
            '--mkfs',
            '--osd-uuid',
            '{uuid}'.format(uuid=uuid),
        ]
        command_check_output(args)

    # change_journal
    journal_path = os.path.join(osd_node, 'journal')
    if file_exists(journal_path):
        # flush_journal
        args = [
            'ceph-osd',
            '-i',
            '{osd_id}'.format(osd_id=osd_id),
            '--flush-journal',
        ]
        command_check_output(args)

        # rm_journal
        os.remove(journal_path)

        # link_journal
        if not hasattr(os, 'symlink'):
            os.symlink = None
        os.symlink('/dev/{journal}'.format(journal=journal_dev), journal_path)

        # recreate_journal
        args = [
            'ceph-osd',
            '-i',
            '{osd_id}'.format(osd_id=osd_id),
            '--mkjournal',
        ]
        command_check_output(args)
        time.sleep(2)

        # ceph_osd_crush
        args = [
            'ceph',
            'osd',
            'crush',
            'add-bucket',
            '{host}'.format(host=curr_host),
            'host',
        ]
        command_check_output(args)
        time.sleep(2)

        # ceph_osd_crush
        args = [
            'ceph',
            'osd',
            'crush',
            'move',
            '{host}'.format(host=curr_host),
            'root=default',
        ]
        command_check_output(args)
        time.sleep(2)

        # ceph_osd_crush
        args = [
            'ceph',
            'osd',
            'crush',
            'add',
            'osd.{osd_id}'.format(osd_id=osd_id),
            '1.0',
            'host={host}'.format(host=curr_host),
        ]
        command_check_output(args)
        time.sleep(2)

    ret['comment'] = 'Create ceph mon node'
    ret['result'] = True
    return ret


if __name__ == '__main__':
    print command_check_output(["du", " -s", "/tmp"])
