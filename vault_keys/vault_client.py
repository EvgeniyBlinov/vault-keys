import os
import hvac
import requests
from hvac import Client

class VaultClient(object):

    """Docstring for VaultClient. """

    def __init__(self, logger, certs=None):
        self.logger = logger
        self.certs = certs


    def get_client(self) -> Client:
        """docstring for get_client"""
        self.logger.debug('Retrieving a vault (hvac) client...')
        vault_client = hvac.Client(
                url=os.getenv('VAULT_ADDR'),
                token=os.getenv('VAULT_TOKEN'),
                cert=self.certs,
        )

        if self.certs:
        # When use a self-signed certificate for the vault service itself, we need to
        # include our local ca bundle here for the underlying requests module.
            rs = requests.Session()
            vault_client.session = rs
            rs.verify = self.certs


        if not vault_client.is_authenticated():
                error_msg = 'Unable to authenticate to the Vault service'
                raise hvac.exceptions.Unauthorized(error_msg)

        return vault_client
