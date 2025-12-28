#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from heatmap_demo.with_js.template import TemplateHTML


###############################################################################
class ChartJS(TemplateHTML):
    template_name = "chartjs.html"


###############################################################################
chartjs = ChartJS()
if __name__ == "__main__":
    chartjs()

