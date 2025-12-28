#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from oak_trade_agent.with_js.template import TemplateHTML


###############################################################################
class BokehJS(TemplateHTML):
    template_name = "bokeh_js.html"


###############################################################################
bokeh_js = BokehJS()
if __name__ == "__main__":
    bokeh_js()