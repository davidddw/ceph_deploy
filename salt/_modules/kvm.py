#!/usr/bin/env python

import logging
import jinja2
import platform
from salt.exceptions import CommandExecutionError
try:
    import libvirt  # pylint: disable=import-error
    HAS_LIBVIRT = True
except ImportError:
    HAS_LIBVIRT = False

import salt.config
import salt.loader

logger = logging.getLogger(__name__)
loglevel = logging.DEBUG
logging.basicConfig(
    level=loglevel,
)

__virtualname__ = 'kvm'


def __virtual__():
    '''
    Rename to ini
    '''
    return __virtualname__


system = platform.system()

if system == "Windows":
    __opts__ = salt.config.minion_config('/etc/salt/minion')
    __salt__ = salt.loader.minion_mods(__opts__)
    __grains__ = salt.loader.grains(__opts__)


class StorageError(Exception):
    """Error while handling storage."""
    pass


def _gen_vol_xml(**context):
    '''
    params: name, host_ips
    '''
    cephpool_template = '''<pool type='rbd'>
  <name>{{ name }}</name>
  <source>
    {% for ip in host_ips -%}
    <host name='{{ ip }}' port='6789'/>
    {% endfor -%}
    <name>{{ name }}</name>
  </source>
</pool>
'''
    jinja_environment = jinja2.Environment()
    template = jinja_environment.from_string(cephpool_template)
    return template.render(**context)


def __get_conn():
    '''
    Detects what type of dom this node is and attempts to connect to the
    correct hypervisor via libvirt.
    '''
    # This has only been tested on kvm and xen, it needs to be expanded to
    # support all vm layers supported by libvirt

    if 'virt.connect' in __opts__:
        conn_str = __opts__['virt.connect']
    else:
        conn_str = 'qemu:///system'

    conn_func = {
        'qemu': [libvirt.open, [conn_str]],
        }

    hypervisor = __salt__['config.get']('libvirt:hypervisor', 'qemu')

    try:
        conn = conn_func[hypervisor][0](*conn_func[hypervisor][1])
    except Exception:
        raise CommandExecutionError(
            'Sorry, {0} failed to open a connection to the hypervisor '
            'software at {1}'.format(
                __grains__['fqdn'],
                conn_func[hypervisor][1][0]
            )
        )
    return conn


def create_storage_pool(name, host_ips):
    xml = _gen_vol_xml(name=name, host_ips=host_ips)

    conn = __get_conn()
    try:
        oldpool = conn.storagePoolLookupByName(name)
        if oldpool is not None:
            p = conn.storagePoolDefineXML(xml, 0)
            p.setAutostart(True)
            p.create(0)
    except libvirt.libvirtError, e:
        logger.error(e)
        raise StorageError(e.get_error_message())

    return p is not None


def define_vol():
    '''
    Define a volume based on the XML passed to the function
    CLI Example:
    .. code-block:: bash
        salt '*' virt.define_vol_xml_str <XML in string format>
    '''
    pools = __salt__['pillar.get']('kvm:pools')
    host_ips = __salt__['pillar.get']('kvm:mon')
    for pool in pools:
        create_storage_pool(pool['name'], host_ips)
