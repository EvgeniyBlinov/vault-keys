#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 ft=python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ._version import __version__


from typing import Callable
import sys,os,getopt
import argparse
import re
import subprocess
import logging

from .vault_parser import VaultTreeParser
from .ansible_vault_crypter import AnsibleVaultCrypter
from .vault_client import VaultClient
from .custom_logger import CustomLogger


class EnvDefault(argparse.Action):
    """Default value for cli args from environment variable"""

    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False

        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class CliRunner(object):

    def __init__(self):
        self.ARGS = "hvVdP"

        self.verbose = False
        self.dry_run = False

        custom_logger = CustomLogger(self.verbose)
        self.logger = custom_logger.getLogger(__name__)

        self._parser = argparse.ArgumentParser(description='vault-keys')
        self.parse_args()

        if self.parsed_args.verbose:
            self.logger.setLevel(logging.INFO)

        if self.parsed_args.dry_run:
            self.vault = None
        else:
            vault_client = VaultClient(self.logger)
            self.vault = vault_client.get_client()


    def parse_args(self):

        self._parser.add_argument(
            '-V', '--version',
            action='version',
            version='%(prog)s {version}'.format(version=__version__))

        self._parser.add_argument(
            "-v", "--verbose",
            default=self.verbose,
            help="increase output verbosity",
            action="store_true")

        self._parser.add_argument(
            "-d", "--dry-run",
            default=self.dry_run,
            help="dry run",
            action="store_true")

        self._parser.add_argument(
            "-k", "--key-file",
            help="run one key file",
            action="store")

        self._parser.add_argument(
            "-K", "--key-dir",
            help="run key directory",
            action="store")

        self._parser.add_argument(
            "-P", "--ansible-vault-password-file",
            help="ansible-vault password file path",
            action=EnvDefault, envvar='ANSIBLE_VAULT_PASSWORD_FILE')

        self._parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
            default=sys.stdin)

        self.parsed_args = self._parser.parse_args()

        if not os.path.isfile(self.parsed_args.ansible_vault_password_file):
            self.logger.fatal('env["ANSIBLE_VAULT_PASSWORD_FILE"] not found!')
            self._parser.print_help(sys.stderr)
            os._exit(1)

        # @TODO:  <01-01-24, Evgeniy Blinov <evgeniy_blinov@mail.ru>> : Add infile
        self.infile = self.parsed_args.infile


    def run(self):

        crypter = AnsibleVaultCrypter(self.parsed_args.ansible_vault_password_file)

        vtp = VaultTreeParser(self.logger, crypter, self.vault, str(self.parsed_args.key_file))
        vtp.parse()

        if self.parsed_args.dry_run:
            vtp.dump_keys()
        else:
            vtp.apply_keys()


def main():
    cli = CliRunner()
    cli.run()

if __name__ == "__main__":
    main()
