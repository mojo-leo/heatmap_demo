#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from oak_trade_agent.with_js.template import TemplateHTML


###############################################################################
class NivoStatic(TemplateHTML):
    template_name = "nivo_static.html"


###############################################################################
nivo_static = NivoStatic()
if __name__ == "__main__":
    nivo_static()
