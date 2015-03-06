#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import with_statement
import os.path as osp

# Twisted import
from twisted.internet import reactor

# CubicWeb import
from logilab.common.configuration import Configuration
from cubes.rql_download.twistedserver.server import CubicWebSSHdFactory


class RsetFTPCommand(object):
    """ Run SFTP server which will connect to a Cubicweb instance to expose
    all the CWSearch entities.
    """
    options = [
        ("cubicweb-instance", {
            "type": "string",
            "default": "brainomics_inst",
            "metavar": "<string>",
            "help": "the sftp server will connect to this cubicweb "
                    "instance."}),
        ("unix-username", {
            "type": "string",
            "default": "toto",
            "metavar": "<string>",
            "help": "the sftp server will read filesystem with the permission "
                    "associated to this user."}),
        ("passphrase", {
            "type": "string",
            "default": "azertyuiop",
            "metavar": "<string>",
            "help": "passphrase."}),
        ("private-key", {
            "type": "string",
            "default": "server_rsa",
            "metavar": "<string>",
            "help": "filepath to private key."}),
        ("public-key", {
            "type": "string",
            "default": "server_rsa.pub",
            "metavar": "<string>",
            "help": "filepath to public key."}),
        ("config-file", {
            "type": "string",
            "default": osp.expanduser("~/.config/rsetftp"),
            "metavar": "<string>",
            "help": "filepath config file (can be overwritten by "
                    "commandline)."}),
        ("base-dir", {
            "type": "string",
            "default": "/",
            "metavar": "<string>",
            "help": "base directory in which file are stored (it acts as "
                    "mask, so every files outside this base-dir will be "
                    "invisible)."}),
        ("port", {
            "type": "int",
            "default": 9999,
            "metavar": "<int>",
            "help": "the sftp server will listen on this port."}),
    ]

    def run(self):
        """ Run the SFTP server.
        """
        config = Configuration(options=self.options, name="twistedsftp")
        config.load_command_line_configuration()
        config.load_file_configuration(config.get("config-file"))
        reactor.listenTCP(config.get("port"), CubicWebSSHdFactory(config))
        print("Twisted server ready on port '{0}'".format(config.get("port")))
        reactor.run()


if __name__ == "__main__":
    RsetFTPCommand().run()
