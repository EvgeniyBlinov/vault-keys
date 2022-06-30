# vault-keys


```
## edit .env
$EDITOR .env

## apply .env
set -o allexport; source .env; set +o allexport

## generate encrypted data
ansible-vault encrypt_string  --name 'value' 'secret_data' | xclip -i

## apply encrypted data to vault
env VERBOSE=1 ./vault_keys.py

```
