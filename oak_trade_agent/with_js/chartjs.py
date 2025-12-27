#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from oak_trade_agent.with_js.template import TemplateHTML


###############################################################################
class ChartJS(TemplateHTML):
    template_name = "chartjs.html"


###############################################################################
chartjs = ChartJS()
if __name__ == "__main__":
    chartjs()

