"""
This file demonstrates how to create a new genie parser and dynamically bind it
into the framework so that a caller can invoke using the device.parse() method,
similar to any other parser that is packaged with the genie framework.

The specific parser is to support the calls:
    "show interface transceiver"
    'show interface {interface} transceiver'

The {interface} parameter can be any form that is accepted by the NXOS CLI.  This includes
ranges, for example:

    In [3]: dev.parse('show interface Ethernet1/1 - 2 transceiver')
    Out[3]:
    {'Ethernet1/1': {
      'vendor': 'CISCO-FINISAR',
      'type': 'Fabric',
      'part_number': 'FTLX8570D3BCL-C2',
      'serial_number': 'FNS1947***'},
     'Ethernet1/2': {
      'vendor': 'CISCO-FINISAR',
      'type': 'Fabric',
      'part_number': 'FTLX8570D3BCL-C2',
      'serial_number': 'FNS1947***'}}

This parser was developed using the genie parsergen "markup" capabilities.  Very nice!

References
-----
https://developer.cisco.com/docs/genie-parsergen/
"""

import re
from copy import copy

from genie import parsergen as pg
from djinnbob.parser.schemas.show_interface_transceiver import ShowInterfaceTransceiverSchema


__all__ = ['ShowInterfaceTransceiver']

OS = 'nxos'

# The following defines a function `find_interface_blocks` that is used to
# locate the start of each interface within the CLI output; see CLI example in
# the parsergen markdown example further down in this file.

_find_interface_blocks = re.compile(r"^(\S+)[\r]?$", re.M).finditer


# -----------------------------------------------------------------------------
#
#                     Genie MetaParser for Device.parse()
#
# -----------------------------------------------------------------------------

class ShowInterfaceTransceiver(ShowInterfaceTransceiverSchema):
    """
    Genie parser for NXOS that collects the interface transceiver inventory
    information.

    The specific parser is to support the calls:
        "show interface transceiver"
        'show interface {interface} transceiver'

    The {interface} parameter can be any form that is accepted by the NXOS cli.  This includes
    ranges, for example:

        In [3]: dev.parse('show interface Ethernet1/1 - 2 transceiver')
        Out[3]:
        {'Ethernet1/1': {
          'vendor': 'CISCO-FINISAR',
          'type': 'Fabric',
          'part_number': 'FTLX8570D3BCL-C2',
          'serial_number': 'FNS194****'},
         'Ethernet1/2': {
          'vendor': 'CISCO-FINISAR',
          'type': 'Fabric',
          'part_number': 'FTLX8570D3BCL-C2',
          'serial_number': 'FNS1947****'}}

    """

    def cli(self, interface=None, output=None, **kwargs):

        # run the command to obtain the TEXT output so that we can then run it
        # through the parsergen.  We do this because if the caller does not
        # provide an interface, or the provided interface is a range, we will
        # need to parse the same output multiple times; once for each interface
        # found in the output.

        cli_cmd = (self.cli_command[0] if not interface
                   else self.cli_command[1].format(interface=interface))

        cli_output = self.device.execute(cli_cmd)

        # extract the list of regular-express match-objects, each starting at
        # the interface name.  We use regex MO so that we can feed each
        # interface block through the parsergen starting each with the
        # interface name.

        if_name_blocks = list(_find_interface_blocks(cli_output))
        if not if_name_blocks:
            # this results in: SchemaEmptyParserError: Parser Output is empty,
            # TODO: investigate the proper way to return empty data so
            #       an exception does not occur.
            return {}

        # declare a dict variable that must returned from this method, and will
        # need to conform to the schema definition.

        schema_output = dict()

        # iterate through each interface found in the CLI TEXT output, running
        # for each through the parsergen system.

        for if_block_mo in if_name_blocks:
            if_name = if_block_mo.group(1)

            parsed = parse_interface_block(
                ifname=if_name,
                cli_text=cli_output[if_block_mo.start():])

            if not parsed:
                continue

            # only create an entry for an interface if a transceiver exists

            schema_output[if_name] = if_schema_data = {}

            # a transceiver exists, so copy the data out from parsergen into
            # the return schema dictionary variable.

            if_schema_data['vendor'] = parsed[f'{MARKUP_PREFIX}.vendor']
            if_schema_data['type'] = parsed[f'{MARKUP_PREFIX}.type']
            if_schema_data['part_number'] = parsed[f'{MARKUP_PREFIX}.part_number']
            if_schema_data['serial_number'] = parsed[f'{MARKUP_PREFIX}.serial_number']

        return schema_output


# -----------------------------------------------------------------------------
#
#                  Genie parsergen markup based parsing
#
# -----------------------------------------------------------------------------

MARKUP_PREFIX = 'if-xcvr'
MARKUP_CONTENT = """
OS: """ + OS.upper() + """
CMD: SHOW_INTF_<NAME>_XCVRS
SHOWCMD: show interface {ifname} transceiver
PREFIX: """ + MARKUP_PREFIX + """

ACTUAL:
Ethernet2/2
    transceiver is present
    type is QSFP-H40G-AOC1M
    name is CISCO
    part number is FCBN410QE2C01-C1
    revision is D
    serial number is ABC19500ABCD
    nominal bitrate is 10300 MBit/sec
    Link length supported for AOC is 1 m
    cisco id is --
    cisco extended id number is 16

MARKUP:
XI<ifname>XEthernet2/2
    transceiver is XR<present>Xpresent
    type is XS<type>XQSFP-H40G-AOC1M
    name is XS<vendor>XCISCO
    part number is XS<part_number>XFCBN410QE2C01-C1
    revision is D
    serial number is XS<serial_number>XABCW19500ABCD
    nominal bitrate is 10300 MBit/sec
    Link length supported for AOC is 1 m
    cisco id is --
    cisco extended id number is 16    
    """

# the parsergen requires a list[tuple] to determine how to process the
# text. in every case, we need to only provide the interface name; and
# then have parsergen extract all other attributes.  The following code
# sets up the dictionary that is then passed as a list of tuple items.

MARKUP_LOOKUP = {f'{MARKUP_PREFIX}.{attr}': None
                 for attr in ['ifname', 'present', 'type',
                              'vendor', 'part_number', 'serial_number']}


pg.extend_markup(MARKUP_CONTENT)


def parse_interface_block(ifname, cli_text):
    lookup = copy(MARKUP_LOOKUP)

    lookup[f'{MARKUP_PREFIX}.ifname'] = ifname

    # the following call will create a parser that we can then invoke
    # notice that we use the device_os and device_output params here to
    # pass the original CLI text output multiple times through
    # parsergen.

    parser = pg.oper_fill(device_os=OS,
                          device_output=cli_text,
                          show_command=('SHOW_INTF_<NAME>_XCVRS', [], {
                              'ifname': ifname
                          }),
                          attrvalpairs=lookup.items(),
                          refresh_cache=False)

    ok = parser.parse()
    if not ok:
        return None

    # If the command was executed and parsed OK, we need to extract it
    # from the parser core data holder.  We use the key 'device_name'
    # include we are using the device_output call above.  Otherwise, we
    # would use the key=self.device.name

    parsed_attrs = pg.ext_dictio['device_name']
    exists = parsed_attrs.get(f'{MARKUP_PREFIX}.present', '') == 'present'

    return parsed_attrs if exists else None

