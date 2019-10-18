# Cisco pyATS Genie - Dynamically add Parsers

This repo showcases a method to dynamically add parsers without having to
clone/fork the
[genieparser](https://github.com/CiscoTestAutomation/genieparser) repository.

User Story:

    As a network automation engineer I need to create my own Genie parsers so
    that when I invoke the Device.parse() method, my parser is found within the
    genie framework and invoked as if it was actually packaged with the Cisco
    genieparser library.
    
The reasons why someone may want to dynamically bind parsers include:

   * Need to develop a set of special-purpose parsers that would not make sense
     to include in the standard genie distribution
     
   * Need to develop set of parsers and deploy into internal systems, and do
     not want to fork the genie distribution during this process.  These parsers
     may ultimately be shared back into the genieparser repo however
     
# Use Case - "show interface transceiver"
    
This repository include a Genie MetaParser that retrieves the interface transceiver information:

    show interface transceiver
    show interface <interface> transceiver

The following NOS are supported:

   * NXOS
   * IOS-XE
       
The `<interface>` parameter can be any supported option, for example on an NXOS device:

    show interface eth1/1 - 48 transceiver
    
# Usage:

Given a Device instance `device`, parse the output of *show interface transceiver*:

````python
import djinnbob

output = device.parse("show interface transceiver")
````

The package `djinnbob` contains the parser and must be explicitly imported so that the parsers within 
this package are properly installed within the genie framework.