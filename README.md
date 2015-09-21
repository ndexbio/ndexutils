# ndex-python-utilities

In addition to python, these utilities require some additional modules.

To install these modules, type the following commands:

```shell
pip install requests
pip install requests-toolbelt
pip install ndex
```

Utility Scripts:

In all scripts that have arguments username and password, these will be the username and password for the NDEx account that you are using. 

upload-to-ndex.py

```shell
python upload-to-ndex.py <username> <password> <directory>
```

Where <i>directory</i> contains all of the network files you want to upload.

create_network_from_tsv.py

```shell
python create_network_from_tsv.py <username> <password> <ndex server> <tsv file> <import plan file> <network name> <network description> 
```
change_network_descriptions.py

change_network_versions.py

make_networks_public.py

make_networks_private.py

delete_all_networks.py

get_user_account_statistics.py

download_pc_pathways.py

```shell
download_pc_pathways.py <datasource> <format>
```

