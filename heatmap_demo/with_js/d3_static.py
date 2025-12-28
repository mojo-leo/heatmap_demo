#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from heatmap_demo.with_js.template import TemplateHTML


###############################################################################
class D3Static(TemplateHTML):
    template_name = "d3_static.html"


###############################################################################
d3_static = D3Static()
if __name__ == "__main__":
    d3_static()
