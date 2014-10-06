#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


options = (
    ("rql_download_log",
      {"type": "string",
      "default": "",
      "help": "base directory in which a 'rql_download.log' file is stored: "
              "if not a valid directory do not log anything.",
      "group": "rql_download", "level": 0,
      }),
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
    ("mountdir",
      {"type": "string",
      "default": "/home/",
      "help": "base directory in which fuse will mount the user virtual "
              "directoies ",
      "group": "rql_download", "level": 0,
      }),
    ("start_sftp_server",
      {"type": "yn",
      "default": False,
      "help": "if true cubicweb will start automatically sftp server "
              "(configured with it is config file, see also README)",
      "group": "rql_download", "level": 0,
      }),
    ("start_user_fuse",
      {"type": "yn",
      "default": False,
      "help": "if true cubicweb will start automatically a fuse mount per user "
              "when the user has some CWSearch entities.",
      "group": "rql_download", "level": 0,
      }),
)

