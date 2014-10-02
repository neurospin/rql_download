#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


options = (
    ("default_expiration_delay",
     {"type": "int",
      "default": 15,
      "help": "specifies expiration delay of CWSearch (in days)",
      "group": "rql_download", "level": 0,
      }),
    ("basedir",
      {"type": "string",
      "default": "/",
      "help": "base directory in which files are stored (this option is given "
              "to the ftp server and fuse processes) ",
      "group": "rql_download", "level": 0,
      }),
    ("start_sftp_server",
      {"type": "yn",
      "default": False,
      "help": "if true cubicweb will start automatically sftp server "
              "(configured with it is config file, see also README)",
      "group": "rql_download", "level": 0,
      }),
)

