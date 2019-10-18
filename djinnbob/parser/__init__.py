# The following bit of genie code is required to bind dinnjob packed into the
# genie import framework.

from genie import abstract
abstract.declare_package(__name__)

# explicitly import the parser module so any geneie parsers defined within are dynamically
# loaded into the genie framework

import djinnbob.parser.iosxe
import djinnbob.parser.nxos
