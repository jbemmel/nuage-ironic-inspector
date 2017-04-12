Hardware introspection for OpenStack Bare Metal - Nuage Plugin
==============================================================

This is an plugin for the auxiliary service for discovering hardware properties for a
node managed by `Ironic`_. Hardware introspection or hardware
properties discovery is a process of getting hardware parameters required for
scheduling from a bare metal node, given it's power management credentials
(e.g. IPMI address, user name and password).

This plugin allows Ironic Inspector to correctly populate LLDP data for Ironic
nodes attached to Nuage Hardware VTEPs (VSG)

To configure, add 'nuage_lldp' to default_processing_hooks in
inspector.conf.


* Free software: Apache license

.. _Ironic: https://wiki.openstack.org/wiki/Ironic

.. note::
    **ironic-inspector** was called *ironic-discoverd* before version 2.0.0.

