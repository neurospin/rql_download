:orphan:

####################
The search mechanism
####################

.. _views_ref:

Description
-----------
This cube provides an action button which shows up if current rset is adaptable in
IFSetAdapter or IEntityAdapter (adpaters also provided by this cube). This button
allows to create a CWSearch entity responsible to store filepath computed by
the adapter from the entities in rset.

.. _views_api:

:mod:`rql_download`: Entities
-----------------------------

.. currentmodule:: rql_download

Adapters
~~~~~~~~

.. autosummary::
    :toctree: generated/adapters/
    :template: class_private.rst

    entities.BaseIDownloadAdapter
    entities.IFSetAdapter
    entities.IEntityAdapter

:mod:`rql_download.views`: Views
--------------------------------

.. currentmodule:: rql_download.views

Components
~~~~~~~~~~

.. autosummary::
    :toctree: generated/views/
    :template: class_private.rst

    components.SaveCWSearchFilterBox
    components.HelpCWSearchBox


Widgets
~~~~~~~

.. autosummary::
    :toctree: generated/views/
    :template: class_private.rst

    cwsearch.CWSearchPathWidget


Cwbrowser utilities
~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/views/
    :template: class_private.rst

    cwsearch_export.CWSearchRsetView
