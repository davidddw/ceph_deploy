#!/usr/bin/env python

import os
import shlex
import subprocess
import re
import tempfile
import logging
import ConfigParser


log = logging.getLogger(__name__)
loglevel = logging.DEBUG
logging.basicConfig(
    level=loglevel,
)


class Line(object):

    """A line in an /etc/fstab line.
    """

    # Lines split this way to shut up coverage.py.
    attrs = ("ws1", "device", "ws2", "directory", "ws3", "fstype")
    attrs += ("ws4", "options", "ws5", "dump", "ws6", "fsck", "ws7")

    def __init__(self, raw):
        self.dict = {}
        self.raw = raw

    def __getattr__(self, name):
        if name in self.dict:
            return self.dict[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        forbidden = ("dict", "dump", "fsck", "options")
        if name not in forbidden and name in self.dict:
            if self.dict[name] is None:
                raise Exception("Cannot set attribute %s when line dies not "
                                "contain filesystem specification" % name)
            self.dict[name] = value
        else:
            object.__setattr__(self, name, value)

    def get_dump(self):
        return int(self.dict["dump"])

    def set_dump(self, value):
        self.dict["dump"] = str(value)

    dump = property(get_dump, set_dump)

    def get_fsck(self):
        return int(self.dict["fsck"])

    def set_fsck(self, value):
        self.dict["fsck"] = str(value)

    fsck = property(get_fsck, set_fsck)

    def get_options(self):
        return self.dict["options"].split(",")

    def set_options(self, slist):
        self.dict["options"] = ",".join(slist)

    options = property(get_options, set_options)

    def set_raw(self, raw):
        match = False

        if raw.strip() != "" and not raw.strip().startswith("#"):
            pat = r"^(?P<ws1>\s*)"
            pat += r"(?P<device>\S*)"
            pat += r"(?P<ws2>\s+)"
            pat += r"(?P<directory>\S+)"
            pat += r"(?P<ws3>\s+)"
            pat += r"(?P<fstype>\S+)"
            pat += r"(?P<ws4>\s+)"
            pat += r"(?P<options>\S+)"
            pat += r"(?P<ws5>\s+)"
            pat += r"(?P<dump>\d+)"
            pat += r"(?P<ws6>\s+)"
            pat += r"(?P<fsck>\d+)"
            pat += r"(?P<ws7>\s*)$"

            match = re.match(pat, raw)
            if match:
                self.dict.update((attr,
                                  match.group(attr)) for attr in self.attrs)

        if not match:
            self.dict.update((attr, None) for attr in self.attrs)

        self.dict["raw"] = raw

    def get_raw(self):
        if self.has_filesystem():
            return "".join(self.dict[attr] for attr in self.attrs)
        else:
            return self.dict["raw"]

    raw = property(get_raw, set_raw)

    def has_filesystem(self):
        """Does this line have a filesystem specification?"""
        return self.device is not None


class Fstab(object):

    """An /etc/fstab file."""

    def __init__(self):
        self.lines = []

    def open_file(self, filespec, mode):
        if type(filespec) in (str, unicode):
            return file(filespec, mode)
        else:
            return filespec

    def close_file(self, f, filespec):
        if type(filespec) in (str, unicode):
            f.close()

    def get_perms(self, filename):
        return os.stat(filename).st_mode  # pragma: no cover

    def chmod_file(self, filename, mode):
        os.chmod(filename, mode)  # pragma: no cover

    def link_file(self, oldname, newname):
        if os.path.exists(newname):
            os.remove(newname)
        if not hasattr(os, 'link'):
            os.link = None
        os.link(oldname, newname)

    def rename_file(self, oldname, newname):
        os.rename(oldname, newname)  # pragma: no cover

    def read(self, filespec):
        """Read in a new file.
        If filespec is a string, it is used as a filename. Otherwise
        it is used as an open file.
        The existing content is replaced.
        """

        f = self.open_file(filespec, "r")
        lines = []
        for line in f:
            lines.append(Line(line))
        self.lines = lines
        self.close_file(filespec, f)

    def write(self, filespec):
        """Write out a new file.
        If filespec is a string, it is used as a filename. Otherwise
        it is used as an open file.
        """

        if type(filespec) in (str, unicode):
            dirname = os.path.dirname(filespec)
            prefix = os.path.basename(filespec) + "."
            fd, tempname = tempfile.mkstemp(dir=dirname, prefix=prefix)
            os.close(fd)
        else:
            tempname = filespec

        f = self.open_file(tempname, "w")
        for line in self.lines:
            f.write(line.raw)
        self.close_file(filespec, f)

        if type(filespec) in (str, unicode):
            self.chmod_file(tempname, self.get_perms(filespec))
            self.link_file(filespec, filespec + ".bak")
            self.rename_file(tempname, filespec)


def set_fstab(device, directory, fstype, options='defaults', dump=0, fsck=0):
    fstab = Fstab()
    fstab.read('/etc/fstab')
    fmt = '{device}\t\t{directory}\t\t{fstype}\t{options}\t {dump} {fsck}\n'
    found = False
    for line in fstab.lines:
        if line.has_filesystem():
            if line.device == device:
                line.directory = directory
                line.fstype = fstype
                line.options = [options]
                line.dump = dump
                line.fsck = fsck
                found = True
            if found:
                break
    if not found:
        line_string = fmt.format(device=device, directory=directory,
                                 fstype=fstype, options=options,
                                 dump=dump, fsck=fsck)
        fstab.lines.append(Line(line_string))
    fstab.write('/etc/fstab')


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


def write_conf(filename, section, option, value):
    conf = ConfigParser.ConfigParser()
    conf.read(filename)
    sections = conf.sections()
    if section not in sections:
        conf.add_section(section)
    conf.set(section, option, value)
    conf.write(open(filename, "w"))


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


mon_path = '/var/lib/ceph/mon'
osd_path = '/var/lib/ceph/osd'
ceph_conf = '/etc/ceph/ceph.conf'


def gen_monmap(cluster, fsid, monmap, hosts_infos):
    host_string = ''
    for host_info in hosts_infos:
        host_fmt = ' --add {host} {ip}:6789 '.format(host=host_info['host'],
                                                     ip=host_info['ip'])
        host_string += host_fmt
    fmt_line = 'monmaptool --cluster={cluster} --create --fsid={fsid} {monmap}'
    command_line = fmt_line.format(cluster=cluster, fsid=fsid, monmap=monmap)
    final_line = command_line + host_string + ' --clobber '
    return command_check_output(final_line)


def ceph_mon_create(cluster, host, monmap):
    fmt_line = 'ceph-mon --cluster={cluster} --mkfs -i {host} \
                --monmap {monmap}'
    command_line = fmt_line.format(cluster=cluster, host=host, monmap=monmap)
    return command_check_output(command_line)


def ceph_mon_start(host):
    fmt_line = 'service ceph start mon.{host}'
    command_line = fmt_line.format(host=host)
    return command(command_line)


def create_mon(cluster, fsid, monmap, curr_host, hosts_infos):

    ret = {'name': 'create_mon',
           'result': False,
           'comment': '',
           'changes': {},
           'data': {}}  # Data field for monitoring state
    # gen_mon_map
    if not path_exists(monmap):
        gen_monmap(cluster, fsid, monmap, hosts_infos)

    # populate_mon
    mon_host = os.path.join(mon_path, 'mon.{host}'.format(host=curr_host))
    if not path_exists(mon_host):
        ceph_mon_create(cluster, curr_host, monmap)

    # start_mon
    ceph_host = os.path.join(
        mon_path,
        '{cluster}-{host}'.format(cluster=cluster, host=curr_host)
    )
    create_mon_path(ceph_host)
    create_done_path(os.path.join(ceph_host, 'done'))

    # start_mon
    if file_exists(os.path.join(ceph_host, 'done')):
        ret['data'].update({'service': ceph_mon_start(curr_host)})

    ret['comment'] = 'Create ceph mon node'
    ret['result'] = True
    return ret


def osd_crush(osd_id, host):
    # ceph_osd_crush
    fmt_line = 'ceph osd crush add-bucket {host} host'
    command_check_output(fmt_line.format(host=host))
    fmt_line = 'ceph osd crush move {host} root=default'
    command_check_output(fmt_line.format(host=host))
    fmt_line = 'ceph osd crush add osd.{osd_id} 1.0 host={host}'
    command_check_output(fmt_line.format(osd_id=osd_id, host=host))


def partiton_exist(value, dev):
    fmt_line = 'sgdisk --print /dev/{dev} | grep {value}'
    return cgrep(fmt_line.format(dev=dev, value=value))


def parted_dev(dev, osd_uuid):
    ptype_tobe = '89c57f98-2fe5-4dc0-89c1-f3ad0ceff2be'
    fmt_line = 'sgdisk --largest-new=1 --change-name="1:ceph data" \
            --partition-guid=1:{osd_uuid} \
            --typecode=1:{ptype_tobe} -- /dev/{dev}'
    return command_check_output(
                fmt_line.format(dev=dev, 
                osd_uuid=osd_uuid,
                ptype_tobe=ptype_tobe))


def mkfs_dev(dev):
    fmt_line = 'mkfs -t xfs -f /dev/{dev}1'
    return command_check_output(fmt_line.format(dev=dev))


def mount_dev(osd_dev, osd_mount_point):
    if not file_exists(osd_mount_point):
        makedir(osd_mount_point)
    fmt_line = 'mount {dev} {mount_point}'
    command_check_output(fmt_line.format(dev=osd_dev,
                                         mount_point=osd_mount_point))
    set_fstab(osd_dev, osd_mount_point, 'xfs')


def replace_journal(osd_node, osd_id, journal_dev, journal_path):
    if file_exists(journal_path):
        # flush_journal
        fmt_line = 'ceph-osd -i {osd_id} --flush-journal'
        command_check_output(fmt_line.format(osd_id=osd_id))
        # rm_journal
        os.remove(journal_path)
        # link_journal
        if not hasattr(os, 'symlink'):
            os.symlink = None
        os.symlink('/dev/{journal}'.format(journal=journal_dev), journal_path)
        # recreate_journal
        fmt_line = 'ceph-osd -i {osd_id} --mkjournal'
        command_check_output(fmt_line.format(osd_id=osd_id))


def ceph_osd_create(osd_id, osd_node, osd_path, uuid):
    fmt_line = 'ceph-osd -i {osd_id} --osd-data={osd} --mkfs --osd-uuid {uuid}'
    command_check_output(
        fmt_line.format(osd_id=osd_id,
                        osd=os.path.join(osd_path, osd_node),
                        uuid=uuid))


def create_osd(osd_id, dev, uuid, journal_dev, curr_host, ex_journal=True):
    ret = {'name': 'create_osd',
           'result': False,
           'comment': '',
           'changes': {},
           'data': {}}  # Data field for monitoring state
    # prepare_disk
    if not partiton_exist('ceph', dev):
        parted_dev(dev, uuid)

    # format_disk
    fmt_line = 'parted -s /dev/{dev} print | grep xfs'
    if not cgrep(fmt_line.format(dev=dev)):
        mkfs_dev(dev)

    # mount_osd
    pattern = 'ceph-{osd_id}'.format(osd_id=osd_id)
    fmt_line = 'ls {osd_path} | grep {pattern}'
    if not cgrep(fmt_line.format(osd_path=osd_path, pattern=pattern)):
        osd_mount_point = os.path.join(osd_path, pattern)
        mount_dev('/dev/{dev}1'.format(dev=dev), osd_mount_point)

    # create_osd
    osd_node = os.path.join(osd_path, 'ceph-{osd_id}'.format(osd_id=osd_id))
    if not file_exists(os.path.join(osd_node, 'ready')):
        ceph_osd_create(osd_id, osd_node, osd_path, uuid)

    # change_journal
    journal_path = os.path.join(osd_node, 'journal')
    if ex_journal:
        replace_journal(osd_node, osd_id, journal_dev, journal_path)

    if file_exists(journal_path):
        # ceph_osd_crush
        osd_crush(osd_id, curr_host)

    ret['comment'] = 'Create ceph mon node'
    ret['result'] = True
    return ret


if __name__ == '__main__':
    set_fstab('/dev/sdd1', '/var/lib/ceph/osd/ceph-3', 'xfs')
