import sys
from copy import copy
from pathlib import Path

from genie import parsergen as pg
from djinnbob.parser.extend import add_parser
from djinnbob.parser.schemas.show_interface_transceiver import ShowInterfaceTransceiverSchema


__all__ = ['ShowInterfaceTransceiver']

OS = Path(__file__).parent.name


class ShowInterfaceTransceiver(ShowInterfaceTransceiverSchema):
    """
    This Genie parser is used to find an extract the interface transceiver
    inventory information, as defined in the Schema.  This parsing requires a
    two step process.  The first is to get the list of interfaces that have
    transceivers using the 'show interface <interface>? transceiver' command.

    Example CLI output:
    -------------------
        If device is externally calibrated, only calibrated values are printed.
        ++ : high alarm, +  : high warning, -  : low warning, -- : low alarm.
        NA or N/A: not applicable, Tx: transmit, Rx: receive.
        mA: milliamperes, dBm: decibels (milliwatts).

                                                   Optical   Optical
                   Temperature  Voltage  Current   Tx Power  Rx Power
        Port       (Celsius)    (Volts)  (mA)      (dBm)     (dBm)
        ---------  -----------  -------  --------  --------  --------
        Te1/1/1      23.7       3.31      32.8      -2.2      -3.9
        Te2/1/2      24.2       3.30      37.5      -2.7      -2.5

    The second step is to execute the "show inventory" command to find values
    that match the "Port" items. While,  Genie provides a parse for this
    command, and the resulting data does not include transceivers (?ugh?). But we can
    use the Port values and the parsegen oper_fill function to get what is needed.

    Example CLI output
    -----------------
        NAME: "Te1/1/1", DESCR: "SFP-10GBase-LR"
        PID: SFP-10G-LR-S        , VID: V01  , SN: FNS21440xxx

        NAME: "Switch 2", DESCR: "C9300-24P"
        PID: C9300-24P         , VID: V02  , SN: FCW2303Gxxx

        NAME: "StackPort2/1", DESCR: "StackPort2/1"
        PID: STACK-T1-50CM     , VID: V01  , SN: MOC2248Axxx

    To extract the information needed, the oper_fill method will be used,
    looping over each of the Port items.
    """

    OPER_TABLE_HEADERS = ['Port', '\(Celsius\)', '\(Volts\)', '\(mA\)', '\(dBm\)', '\(dBm\)']
    OPER_TABLE_LABLES = ['port', 'temp', 'voltage', 'current', 'tx_pow', 'rx_pow']

    def cli(self, interface=None):
        # run the command to obtain the TEXT output so that we can then run it
        # through the parsergen.  We do this because if the caller does not
        # provide an interface, or the provided interface is a range, we will
        # need to parse the same output multiple times; once for each interface
        # found in the output.

        cli_cmd = (self.cli_command[0] if not interface
                   else self.cli_command[1].format(interface=interface))

        oper_res = pg.oper_fill_tabular(device=self.device,
                                        show_command=cli_cmd,
                                        header_fields=self.OPER_TABLE_HEADERS,
                                        label_fields=self.OPER_TABLE_LABLES)

        # declare a dict variable that must returned from this method, and will
        # need to conform to the schema definition.

        schema_output = dict()

        if_names = list(oper_res.entries)
        if not if_names:
            return schema_output

        cli_inventory = self.device.execute("show inventory")
        for if_name in if_names:
            schema_output[if_name] = if_schema_data = {}

            data = parse_inventory_for_interface(if_name, cli_inventory)
            if not data:
                continue

            if_schema_data['type'] = data[f'{MARKUP_PREFIX}.type']
            # vendor is not supported on this platform?
            if_schema_data['part_number'] = data[f'{MARKUP_PREFIX}.part_number']
            if_schema_data['serial_number'] = data[f'{MARKUP_PREFIX}.serial_number']

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
NAME: "Te1/1/1", DESCR: "SFP-10GBase-LR"
PID: SFP-10G-LR-S        , VID: V01  , SN: FNS21440xxx


MARKUP:
NAME: "XQ<ifname>XTe1/1/1", DESCR: "XQ<type>XSFP-10GBase-LR"
PID: XS<part_number>XSFP-10G-LR-SX        , VID: V01  , SN: XS<serial_number>XFNS214401111

"""

pg.extend_markup(MARKUP_CONTENT)

MARKUP_LOOKUP = {f'{MARKUP_PREFIX}.{attr}': None
                 for attr in ['ifname', 'type', 'part_number', 'serial_number']}


def parse_inventory_for_interface(ifname, inventory_output):
    lkup = copy(MARKUP_LOOKUP)
    lkup[f'{MARKUP_PREFIX}.ifname'] = ifname

    parser = pg.oper_fill(device_os=OS,
                          device_output=inventory_output,
                          show_command=('SHOW_INTF_<NAME>_XCVRS', [], {
                              'ifname': ifname
                          }),
                          attrvalpairs=lkup.items(),
                          refresh_cache=False)

    ok = parser.parse()
    return None if not ok else pg.ext_dictio['device_name']


# -----------------------------------------------------------------------------
#
#                  Dynamically extend genie parsers
#
# -----------------------------------------------------------------------------

# This call dynamically add this parser to the parsegen framework; it must be
# after the the class definition.

add_parser(mod=sys.modules[__name__], package=__package__,
           os_name='iosxe', parser=ShowInterfaceTransceiver)
