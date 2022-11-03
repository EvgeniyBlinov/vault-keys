import codecs
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import PromptVaultSecret, get_file_vault_secret
from ansible.parsing.vault import VaultEditor, VaultLib, match_encrypt_secret
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


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
