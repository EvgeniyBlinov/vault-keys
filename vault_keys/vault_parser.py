#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 ft=python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import hvac

from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


class VaultTreeParser(object):

    """Docstring for VaultTreeParser. """


    def __init__(self, logger, crypter, vault, base_dir):
        """TODO: to be defined. """
        self.logger = logger
        self.crypter = crypter
        self.vault = vault
        self.base_dir = base_dir
        self.keys = []

    def remove_prefix(self, text: str, prefix: str) -> str:
        if text.startswith(prefix):
            return text[len(prefix):]
        return text


    def read_key_data(self, key: dict) -> dict:
        if "value" in key:
            return {'value': str(key['value'])}
        if "token" in key:
            return {'token': str(key['token'])}
        if "tls.key" in key and 'tls.crt' in key:
            return {'tls.crt': str(key['tls.crt']), 'tls.key': str(key['tls.key'])}


    def read_all_keys(self, crypter: AnsibleVaultEncryptedUnicode,  keys_file: str, path: str) -> list:
        """docstring for read_all_keys"""
        keys = []

        file_keys = crypter.yaml_load(keys_file)
        for key in file_keys:
            keys.append({os.path.join(path, key['path']): self.read_key_data(key)})

        return keys


    def read_one_key(self, crypter: AnsibleVaultEncryptedUnicode, key_file: str, path: str) -> list:
        """docstring for read_one_key"""
        return [{path: self.read_key_data(crypter.yaml_load(key_file))}]


    def parse_dirs(self, path=None):
        """docstring for parse_dirs"""
        if not path:
            path = self.base_dir

        for root, dirs, files in os.walk(path):
            if len(files):
                path = self.remove_prefix(root, self.base_dir)
                for file in files:
                    self.parse_key_file(os.path.join(root, file), path)


    def parse_key_file(self, key_file, path):
        """docstring for parse_key_file"""
        if '__ALL__' in key_file:
            self.keys = self.keys + self.read_all_keys(self.crypter, key_file, path)
        else:
            self.keys = self.keys + self.read_one_key(self.crypter, key_file, path)


    def vault_read_secret(self, key, mount_point="secret"):
        """docstring for vault_read_key"""
        data = None
        try:
            read_response = self.vault.secrets.kv.v2.read_secret_version(
                mount_point=mount_point,
                path=key,
                )
            data = read_response['data']['data']
        except hvac.exceptions.InvalidPath as e:
            pass

        return data


    def vault_update_secret(self, key, value,  mount_point="secret"):
        """docstring for vault_update_secret"""
        try:
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
        """docstring for apply_keys"""
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
        """docstring for dump_keys"""
        for key in self.keys:
            for key_name, key_value in key.items():
                print("%s=%s" % (key_name, json.dumps(key_value)))
