#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 ft=python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import hvac
import logging
import typing

from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from .ansible_vault_crypter import AnsibleVaultCrypter


class VaultTreeParser(object):

    """VaultTreeParser for parsing Ansible-vault encrypted keys"""


    def __init__(self, logger: logging.Logger, crypter: AnsibleVaultCrypter, vault: typing.Optional[hvac.Client], key_file: str='', base_dir: str='./kv/', all_filename: str='__ALL__'):
        """Init VaultTreeParser"""
        self.logger = logger
        self.crypter = crypter
        self.vault = vault
        self.key_file = key_file
        self.base_dir = base_dir
        self.all_filename = all_filename
        self.keys = []

    def remove_prefix(self, text: str, prefix: str) -> str:
        """Remove path prefix"""
        if text.startswith(prefix):
            return text[len(prefix):]
        return text


    def read_key_data(self, key: dict) -> dict:
        """ Read key content (value|token|tls.key)"""
        key_data = {}
        if "value" in key:
            key_data = {'value': str(key['value'])}
        if "token" in key:
            key_data = {'token': str(key['token'])}
        if "tls.key" in key and 'tls.crt' in key:
            key_data = {'tls.crt': str(key['tls.crt']), 'tls.key': str(key['tls.key'])}

        return key_data


    def read_all_keys(self, crypter: AnsibleVaultCrypter,  keys_file: str, path: str) -> list:
        """Read all keys content by VaultTreeParser.read_key_data()"""
        keys = []

        file_keys = crypter.yaml_load(keys_file)
        for key in file_keys:
            keys.append({os.path.join(path, key['path']): self.read_key_data(key)})

        return keys


    def read_one_key(self, crypter: AnsibleVaultCrypter, key_file: str, path: str) -> list:
        """Read one key content by VaultTreeParser.read_key_data()"""
        return [{path: self.read_key_data(crypter.yaml_load(key_file))}]


    def parse_dirs(self, path: typing.Optional[str]=None):
        """Parsing keys dir"""
        if not path:
            path = self.base_dir

        for root, dirs, files in os.walk(path):
            if len(files):
                path = self.remove_prefix(root, self.base_dir)
                for file in files:
                    self.parse_key_file(os.path.join(root, file), path)


    def parse_key_file(self, key_file, path: str):
        """Parsing file with keys"""
        if '__ALL__' in key_file:
            self.keys = self.keys + self.read_all_keys(self.crypter, key_file, path)
        else:
            self.keys = self.keys + self.read_one_key(self.crypter, key_file, path)


    def vault_read_secret(self, key, mount_point: str="secret"):
        """Read Hashicorp Vault secret"""
        data = None
        try:
            if self.vault:
                read_response = self.vault.secrets.kv.v2.read_secret_version(
                    mount_point=mount_point,
                    path=key,
                    )
                data = read_response['data']['data']
        except hvac.exceptions.InvalidPath as e:
            pass

        return data


    def vault_update_secret(self, key, value,  mount_point: str="secret"):
        """Update Hashicorp Vault secret"""
        try:
            if self.vault:
                create_response = self.vault.secrets.kv.v2.create_or_update_secret(
                    path=key,
                    secret=value,
                    mount_point=mount_point
                )
                self.logger.info("%s: %s" % (key, json.dumps(create_response)))
        except hvac.exceptions.InvalidRequest as e:
            self.logger.error('Error: InvalidRequest %s : %s' % (key, str(e)))

        return None


    def apply_keys(self):
        """Apply all Hashicorp Vault secrets"""
        for key in self.keys:
            for key_path, value in key.items():
                kv_parts = key_path.split('/')
                kv_name = kv_parts.pop(0)
                kv_key_path = '/'.join(kv_parts)

                old_key_value = self.vault_read_secret(kv_key_path, mount_point=kv_name)

                if old_key_value and  old_key_value == value:
                    self.logger.info("%s: %s" % (key_path, 'Key data is already exists.'))
                else:
                    self.vault_update_secret(kv_key_path, value, mount_point=kv_name)


    def dump_keys(self):
        """Dump all keys"""
        for key in self.keys:
            for key_name, key_value in key.items():
                print("%s=%s" % (key_name, json.dumps(key_value)))


    def parse(self):
        """Parse keys"""
        if self.key_file and os.path.isfile(self.key_file):
            key_path = self.key_file.replace(self.base_dir, "")
            if self.all_filename in key_path:
                key_path = key_path.replace("/" + self.all_filename, "")
            self.parse_key_file(self.key_file, key_path)
        else:
            self.parse_dirs(self.base_dir)
