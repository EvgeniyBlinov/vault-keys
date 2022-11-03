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

from .vault_parser import VaultTreeParser
from .ansible_vault_crypter import AnsibleVaultCrypter
from .vault_client import VaultClient
from .custom_logger import CustomLogger


class CliRunner(object):

    def __init__(self):
        self.ARGS = "hvVd"

        self.verbose = False
        self.dry_run = False
        self.key_file = None
        self.key_dir = None

        self.parse_args()


    def parse_args(self):
        parser = argparse.ArgumentParser(description='vault-keys')

        parser.add_argument(
            '-V', '--version',
            action='version',
            version='%(prog)s {version}'.format(version=__version__))

        parser.add_argument(
            "-v", "--verbose",
            help="increase output verbosity",
            action="store_true")

        parser.add_argument(
            "-d", "--dry-run",
            help="dry run",
            action="store_true")

        parser.add_argument(
            "-k", "--key-file",
            help="run one key file",
            action="store")

        parser.add_argument(
            "-K", "--key-dir",
            help="run key directory",
            action="store")

        parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
            default=sys.stdin)

        args = parser.parse_args()

        if args.verbose or os.getenv('VERBOSE'):
            self.verbose = True
        if args.dry_run or os.getenv('DRY_RUN'):
            self.dry_run = True

        if args.key_dir:
            self.key_dir = args.key_dir
        if args.key_file:
            self.key_file = args.key_file

        self.infile = args.infile

    def run(self):

        custom_logger = CustomLogger(self.verbose)
        logger = custom_logger.getLogger(__name__)

        vault_password_file = os.getenv('ANSIBLE_VAULT_PASSWORD_FILE')
        crypter = AnsibleVaultCrypter(vault_password_file)

        if self.dry_run:
            vault = None
        else:
            vault_client = VaultClient(logger)
            vault = vault_client.get_client()

        KV_BASE_DIR = "./kv/"

        vtp = VaultTreeParser(logger, crypter, vault, KV_BASE_DIR)

        if self.key_file:
            key_path = self.key_file.replace(KV_BASE_DIR, "")
            if "__ALL__" in key_path:
                key_path = key_path.replace("/__ALL__", "")
            vtp.parse_key_file(self.key_file, key_path)
        else:
            vtp.parse_dirs(self.key_dir)

        if self.dry_run:
            vtp.dump_keys()
        else:
            vtp.apply_keys()


def main():
    cli = CliRunner()
    cli.run()

if __name__ == "__main__":
    main()
