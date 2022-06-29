# vault-keys


```
$EDITOR .env

set -o allexport; source .env; set +o allexport

env VERBOSE=1 ./vault_keys.py

ansible-vault encrypt_string  --name 'value' 'secret_data' | xclip -i
```
