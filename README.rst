ndex-python-utilities
=====================

**Warning: This repository is for development and features may change.
Please use this at your own risk.**


Dependencies
------------

* `ndex2 <https://pypi.org/project/ndex2>`_
* `networkx <https://pypi.org/project/networkx>`_
* `ndexutil <https://pypi.org/project/ndexutil>`_
* `biothings_client <https://pypi.org/project/biothings-client>`_
* `requests <https://pypi.org/project/requests>`_
* `requests-toolbelt <https://pypi.org/project/requests_toolbelt>`_
* `pandas <https://pypi.org/project/pandas>`_
* `mygene <https://pypi.org/project/mygene>`_
* `enum34 <https://pypi.org/project/enum34>`_
* `jsonschema <https://pypi.org/project/jsonschema>`_
* `urllib3 <https://pypi.org/project/urllib3>`_

Compatibility
-------------

* Python 3.3+

Installation
------------

.. code-block::

   git clone https://github.com/ndexbio/ndexutils
   cd ndexutils
   make dist
   pip install dist/ndexutil*whl

OR via `PyPI <https://pypi.org/ndexutils>`_

.. code-block::

   pip install ndexutil


TSV Loader
----------

This module contains the Tab Separated Variable Loader (TSV Loader) which generates
an `NDEx CX <http://www.home.ndexbio.org/data-model/>`_ file from a tab separated
text file of edge data and attributes.

To load data a load plan must be created. This plan tells the loader how to map the
columns in the file to nodes, and edges. This load plan needs to validate against
`this load plan JSON schema <https://github.com/ndexbio/ndexutils/blob/master/ndexutil/tsv/loading_plan_schema.json>`_

**Example TSV file**

.. code-block::

    SOURCE  TARGET  WEIGHT
    ABCD    AAA1    0.555
    GGGG    BBBB    0.305

**SOURCE** is the source node, **TARGET** is target node

A schema that could be:

.. code-block::

    {
    "source_plan":
        {
            "node_name_column": "SOURCE"
        },
        "target_plan":
        {
            "node_name_column": "TARGET"
        },
        "edge_plan":
        {
            "default_predicate": "unknown",
            "property_columns": [
              {
                "column_name": "WEIGHT",
                "attribute_name": "weight",
                "data_type": "double"
              }
            ]
        }
    }



Example below assumes the following:

* **./loadplan.json** is the load plan in JSON format
* **./style.cx** is a `NDEx CX <http://www.home.ndexbio.org/data-model/>`_ with a style.

.. code-block::

    import ndex2
    from ndexutil.tsv.streamtsvloader import StreamTSVLoader

    # using ndex2 client library read CX file as NiceCXNetwork object
    style_network = ndex2.create_nice_cx_from_file('./style.cx')

    loader = StreamTSVLoader('./loadplan.json', style_network)
    with open('./input.tsv', 'r') as tsvfile:
        with open('./output.cx', 'w') as outfile:
            loader.write_cx_network(tsvfile, outfile)


Credits
-------

