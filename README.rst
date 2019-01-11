ndex-python-utilities
=====================

**Warning: This repository is for development and features may change.
Please use this at your own risk.**

In addition to python, these utilities require some additional modules.

To install these modules, type the following commands:

.. code:: shell

    pip install requests
    pip install requests-toolbelt
    pip install ndex2
    pip install networkx==1.11
    pip install pandas
    pip install jsonschema

Utility Scripts:

In all scripts that have arguments username and password, these will be
the username and password for the NDEx account that you are using.

upload-to-ndex.py

.. code:: shell

    python upload-to-ndex.py <username> <password> <directory>

Where directory contains all of the network files you want to upload.

create\_network\_from\_tsv.py

.. code:: shell

    python create_network_from_tsv.py <username> <password> <ndex server> <tsv file> <import plan file> <network name> <network description> 

change\_network\_descriptions.py

change\_network\_versions.py

make\_networks\_public.py

make\_networks\_private.py

delete\_all\_networks.py

get\_user\_account\_statistics.py

download\_pc\_pathways.py

.. code:: shell

    download_pc_pathways.py <datasource> <format>

