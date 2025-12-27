#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from oak_trade_agent.with_js.template import TemplateHTML


###############################################################################
class ECharts(TemplateHTML):
    template_name = "echarts.html"


###############################################################################
echarts = ECharts()
if __name__ == "__main__":
    echarts()
