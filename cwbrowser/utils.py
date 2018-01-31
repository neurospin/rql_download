##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2018
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
A module with common functions.
"""

# System import
import getpass


def logo():
    """ Logo is ascii art using dancing font.

    Returns
    -------
    logo: str
        the pisap logo.
    """
    logo = """
   ____                 ____     ____    U  ___ u              ____   U _____ u   ____     
U /"___| __        __U | __")uU |  _"\\ u  \\/"_ \\/__        __ / __"| u\\| ___"|/U |  _"\\ u  
\\| | u   \\"\\      /"/ \\|  _ \\/ \\| |_) |/  | | | |\\"\\      /"/<\\___ \\/  |  _|"   \\| |_) |/  
 | |/__  /\\ \\ /\\ / /\\  | |_) |  |  _ <.-,_| |_| |/\\ \\ /\\ / /\\ u___) |  | |___    |  _ <    
  \\____|U  \\ V  V /  U |____/   |_| \\_\\\\_)-\\___/U  \\ V  V /  U|____/>> |_____|   |_| \\_\\   
 _// \\\\ .-,_\\ /\\ /_,-._|| \\\\_   //   \\\\_    \\\\  .-,_\\ /\\ /_,-. )(  (__)<<   >>   //   \\\\_  
(__)(__) \\_)-'  '-(_/(__) (__) (__)  (__)  (__)  \\_)-'  '-(_/ (__)    (__) (__) (__)  (__) 
"""
    return logo


def ask_credential(login=None, password=None):
    """ Ask for a login and a password when not specified.

    Parameters
    ----------
    login: str, default None
        a login.
    password: str, defualt None
        a password.

    Returns
    -------
    login: str, default None
        a login.
    password: str, defualt None
        a password.
    """
    if login is None:
        login = raw_input("Login:")
    if password is None:
        password = getpass.getpass("Password for " + login + ":")
    return login, password
