"""
This file defines the Genie parser schema for the "show interface transceiver"
use-case.  This file is located in a shared/common folder (schemas) so that
different Device OS parsers have a shared schema definition.
"""

from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import Any, Optional

__all__ = ["ShowInterfaceTransceiverSchema"]


class ShowInterfaceTransceiverSchema(MetaParser):
    """
    Schema definition for parser: "show interface <interface> transceiver"
    """
    schema = {
        Any(): {                                        # key is the interface-name
            Optional('vendor'): str,
            Optional('type'): str,
            Optional('part_number'): str,
            Optional('serial_number'): str,
        }
    }

    # The following lists the supported commands that can be passed to the
    # Device.parse() method.  Each NOS parser must support both.

    cli_command = [
        'show interface transceiver',
        'show interface {interface} transceiver'
    ]
