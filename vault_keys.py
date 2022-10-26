#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 ft=python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import codecs

from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import PromptVaultSecret, get_file_vault_secret
from ansible.parsing.vault import VaultEditor, VaultLib, match_encrypt_secret
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


import hvac
import requests
import logging


def get_vault_client(logger, certs=None):
        logger.debug('Retrieving a vault (hvac) client...')
        vault_client = hvac.Client(
                url=os.getenv('VAULT_ADDR'),
                token=os.getenv('VAULT_TOKEN'),
                cert=certs,
        )

        if certs:
        # When use a self-signed certificate for the vault service itself, we need to
        # include our local ca bundle here for the underlying requests module.
            rs = requests.Session()
            vault_client.session = rs
            rs.verify = certs


        if not vault_client.is_authenticated():
                error_msg = 'Unable to authenticate to the Vault service'
                raise hvac.exceptions.Unauthorized(error_msg)

        return vault_client



class AnsibleVaultCrypter(object):

    """Docstring for AnsibleVaultCrypter """


    def __init__(self, vault_password_file):
        loader = DataLoader()
        secret = get_file_vault_secret(filename=vault_password_file, loader=loader)
        secret.load()
        vault_secrets = [('default', secret)]

        self._vault = VaultLib(vault_secrets)


    def yaml_load(self, file: str):
        """docstring for yaml_load"""
        loaded_yaml = None
        with codecs.open(file, 'r', encoding='utf-8') as f:
            loaded_yaml = AnsibleLoader(f, vault_secrets=self._vault.secrets).get_single_data()
        return loaded_yaml



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


    def parse_dirs(self, path=None):
        """docstring for parse_dirs"""
        if not path:
            path = self.base_dir

        for root, dirs, files in os.walk(path):
            if len(files):
                path = self.remove_prefix(root, self.base_dir)
                for file in files:
                    if file == '__ALL__':
                        self.keys = self.keys + self.read_all_keys(self.crypter, os.path.join(root, file), path)


    def apply_keys(self):
        """docstring for apply_keys"""
        for key in self.keys:
            for key_path, value in key.items():
                kv_parts = key_path.split('/')
                kv_name = kv_parts.pop(0)
                kv_key_path = '/'.join(kv_parts)

                old_key_value = None
                try:
                    read_response = self.vault.secrets.kv.v2.read_secret_version(
                        mount_point=kv_name,
                        path=kv_key_path,
                        )
                    old_key_value = read_response['data']['data']
                except hvac.exceptions.InvalidPath as e:
                    pass

                if old_key_value and  old_key_value == value:
                    self.logger.info("%s: %s" % (key_path, 'Key data is already exists.'))
                else:
                    try:
                        create_response = self.vault.secrets.kv.v2.create_or_update_secret(
                            path=kv_key_path,
                            secret=value,
                            mount_point=kv_name
                        )
                        self.logger.info("%s: %s" % (key_path, json.dumps(create_response)))
                    except hvac.exceptions.InvalidRequest as e:
                        self.logger.error('Error: InvalidRequest %s : %s' % (kv_key_path, str(e)))


    def dump_keys(self):
        """docstring for dump_keys"""
        for key in self.keys:
            for key_name, key_value in key.items():
                print("%s=%s" % (key_name, json.dumps(key_value)))




def main():
    """docstring for main"""
    logger = logging.getLogger(__name__)

    # create console handler and set level to debug
    ch = logging.StreamHandler()

    dry_run = False
    if os.getenv('DRY_RUN'):
        dry_run = True

    if os.getenv('VERBOSE'):
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    vault_password_file = os.getenv('ANSIBLE_VAULT_PASSWORD_FILE')
    crypter = AnsibleVaultCrypter(vault_password_file)

    if dry_run:
        vault = None
    else:
        vault = get_vault_client(logger)

    KV_BASE_DIR = "./kv/"

    vtp = VaultTreeParser(logger, crypter, vault, KV_BASE_DIR)
    vtp.parse_dirs()

    if dry_run:
        vtp.dump_keys()
    else:
        vtp.apply_keys()

if __name__ == '__main__':
    main()
