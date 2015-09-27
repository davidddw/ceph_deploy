#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# @author: david_dong

import sys
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

try:
    from livecloud import deploy_salt
    from livecloud import deploy_ceph
    from livecloud import util
except ImportError:
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.split(sys.argv[0])[0], "..")))


def parser_arg(argv=None):
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_description = "This is used for building ceph evn by saltstack"
    program_name = os.path.basename(sys.argv[0])

    try:
        parser = ArgumentParser(description=program_description,
                                formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument(
            "-p", "--prepair", dest="prepair", action="store_true",
            help="generate prepair config in pillar [default: %(default)s]")
        parser.add_argument(
            "-d", "--deploy_minion", dest="interface",
            help="deploy minion by nic ")
        parser.add_argument(
            "-s", "--highstate", dest="highstate", action="store_true",
            help="set ceph node state.highstate [default: %(default)s]")
        parser.add_argument(
            "-n", "--ntp", dest="ntp", action="store_true",
            help="set ntp state [default: %(default)s]")
        parser.add_argument(
            "-i", "--install", dest="package",
            help="update 'ceph' or 'kvm'")
        parser.add_argument(
            "-c", "--ceph", dest="ceph",
            help="deploy ceph 'journal' 'mon' 'osd'")
        # Process arguments
        args = parser.parse_args()

        if (not args.prepair and args.interface is None and
                not args.highstate and not args.ntp and
                args.package is None and args.ceph is None):
            parser.print_help()
            sys.exit()

        if args.prepair:
            util.output_title('prepair livecloud env')
            deploy_salt.prepair_livecloud_conf()
            return 0

        if args.interface:
            util.output_title('delpoy salt minion')
            deploy_salt.deploy_salt_minion(args.interface)
            return 0

        if args.highstate:
            util.output_title('Setting highstate by salt')
            deploy_ceph.execute_salt_sls('state.highstate')
            return 0

        if args.ntp:
            util.output_title('Setting ntp state by salt')
            deploy_ceph.execute_salt_sls('state.sls', ['ceph.ntp'])
            return 0

        if args.package == 'ceph':
            util.output_title('Update ceph packages')
            deploy_ceph.execute_salt_sls('state.sls', ['ceph.ceph'])
            return 0
        elif args.package == 'kvm':
            util.output_title('Update kvm packages')
            deploy_ceph.execute_salt_sls('state.sls', ['ceph.kvm'])
            return 0

        if args.ceph == 'mon':
            util.output_title('deploy mon by saltstack')
            deploy_ceph.execute_salt_modules('ceph.mon')
            return 0

        if args.ceph == 'osd':
            util.output_title('deploy osd by saltstack')
            deploy_ceph.execute_salt_modules('ceph.osd')
            return 0

        if args.ceph == 'journal':
            util.output_title('deploy journal by saltstack')
            deploy_ceph.execute_salt_modules('ceph.journal')
            return 0

        return 0
    except KeyboardInterrupt:
        return 0
    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2


if __name__ == '__main__':
    parser_arg()
