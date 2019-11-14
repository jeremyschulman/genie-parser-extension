# This file contains the entry_point callable that is responsible for
# dynamically adding the parsers into the Genie framework.

from djinnbob.parser import iosxe, nxos

__all__ = []


def add_my_parsers():
    """
    This function is called during the genie.libs.parser startup to dynamically load
    parsers defined in the djinnbob package.

    Returns
    -------
    dict[list]
        key: <str> - OS name, for example "nxos"
        value: list[class<MetaParser>] - list of parser classes
    """

    return {
        'iosxe': [
            iosxe.show_interface_transceiver.ShowInterfaceTransceiver
        ],
        'nxos': [
            nxos.show_interface_transceiver.ShowInterfaceTransceiver
        ]
    }
