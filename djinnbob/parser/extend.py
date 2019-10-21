"""
This file provides the mechanism to add a user-defined parse into the genie
parser framework.
"""

# Genie maintains all known parsers in a global dictionary called
# `parser_data`.  The add_parser() function will write into this data to
# dynamically bind user-defined parsers into the Genie framework.

from genie.libs.parser.utils.common import parser_data


def add_parser(mod, parser, os_name):
    """
    Dynamically add the parser class to the Genie parser framework.

    For example usage, see the 'nxos/show_interface_transceiver.py' file

    Parameters
    ----------
    mod : module
        The module where the parser is located

    parser : class
        The parser class that implements a MetaParser

    os_name : str
        The NOS name for which the parser is supported, for example "nxos"
    """
    package = mod.__package__

    for cmd in parser.cli_command:
        if cmd not in parser_data:
            parser_data[cmd] = {}

        parser_data[cmd][os_name] = {
            'module_name': mod.__name__.rsplit('.', 1)[-1],
            'package': package,
            'class': parser.__name__
        }
