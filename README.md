[![MIT License][license-image]][license-url]

# vault-keys

## Usage

```
## edit .env
$EDITOR .env

## apply .env
set -o allexport; source .env; set +o allexport

## generate encrypted data
ansible-vault encrypt_string  --name 'value' 'secret_data' | xclip -i

## apply encrypted data to vault
vault_keys.py -v

## dump only encryped data without applying
vault_keys.py -d

## dump only one key file
vault-keys -v -d -k ./kv/secret/ldap2/keycloak/user_dn
```

## Test

```
echo 123 > ~/vault-token-test

cat > .env <<EOF
ANSIBLE_VAULT_PASSWORD_FILE=~/vault-token-test
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=myroot
EOF

python3 -m venv .python
source .python/bin/activate
set -o allexport; source .env; set +o allexport
python3 -m pip install git+https://github.com/EvgeniyBlinov/vault-keys.git


mkdir -p ./kv/secret/ldap2/keycloak
curl https://raw.githubusercontent.com/EvgeniyBlinov/vault-keys/main/kv/secret/ldap2/keycloak/user_dn -o ./kv/secret/ldap2/keycloak/user_dn

vault-keys -v -d -k ./kv/secret/ldap2/keycloak/user_dn
```

### DEBUG

Debug module from local directory

```
python3 -m pip install -e .
```

Install from dir for installation checking

```
python3 -m pip install -U  git+file://${PWD} vault-keys
```

## License

[![MIT License][license-image]][license-url]

## Author

- [Blinov Evgeniy](mailto:evgeniy_blinov@mail.ru) ([http://blinov.in.ua/](http://blinov.in.ua/))

[license-image]: http://img.shields.io/badge/license-MIT-blue.svg?style=flat
[license-url]: LICENSE
