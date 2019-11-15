=======
History
=======

0.8.0 2019-11-15
------------------

* Fixed bug in StreamTSVLoader where 2 \@context network attributes were added to network if \@context was set in load plan and \@context was passed in the network attributes parameter for `write_cx_network()`

* Added new command to **ndexmisctools.py** named *tsvloader* that lets caller load TSV files as networks into NDEx

0.7.0 2019-09-11
-----------------

* Added new command to **ndexmisctools.py** named *systemproperty* that lets
  caller update showcase, visibility, and indexing for a single network or
  all networks in a networkset in NDEx

0.6.1 2019-07-12
----------------

* Fixed bug where **ndexmisctools.py** *networkattributeupdate* was creating
  duplicate network attributes for name, description, and value. This is
  due to server bug. To deal with this the code removes those entries when
  doing the network attribute update and forbids caller from trying to
  update those attributes

0.6.0 2019-07-10
----------------

* Added new commandline utility *ndexmisctools.py* which lets caller
  copy a network from one NDEx account to another and lets one update
  network attributes of a network in NDEx.
  WARNING: THIS IS AN UNTESTED ALPHA RELEASE AND MAY CONTAIN ERRORS

0.5.0 2019-06-06
----------------

* Added GeneSymbolSearcher class to loaderutils.py module

* Minor bug fix in NetworkIssueReport get_fullreport_as_string() where
  issue text is wrapped in str() in case its not a string 

0.4.0 2019-05-23
----------------

* Added loaderutils.py module with two new classes, NetworkIssueReport and
  an abstract class NetworkUpdator

0.3.0 2019-05-14
----------------

* tsv2nicecx2.convert_pandas_to_nice_cx_with_load_plan now loads @context
  data into a @context network attribute instead of a separate aspect

0.2.0 2019-04-01
----------------

* StreamTSVLoader class added which enables loading of TSV data into
  in streaming format to handle loading of large networks



