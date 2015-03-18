:orphan:

####################
Schema modifications
####################

.. _schema_ref:

Description
-----------
The database schema has been modified and a CWSearch entity has been added.
When a search is processed, a CWSearch entity is created. This latter is
responsible to store filepath computed by the adapter from the entities in rset.

.. _schema_api:

:mod:`rql_download`: Schema
---------------------------

.. currentmodule:: rql_download

.. autosummary::
    :toctree: generated/schema/
    :template: class_private.rst

    schema.CWSearch

:mod:`rql_download`: Associated hooks
-------------------------------------

.. autosummary::
    :toctree: generated/schema/
    :template: class_private.rst

    hooks.CWSearchAdd
    hooks.CWSearchExpirationDateHook
    hooks.CWSearchDelete
