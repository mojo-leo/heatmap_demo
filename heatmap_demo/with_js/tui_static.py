#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from heatmap_demo.with_js.template import TemplateHTML


###############################################################################
class TUIStatic(TemplateHTML):
    template_name = "tui_static.html"


###############################################################################
tui_static = TUIStatic()
if __name__ == "__main__":
    tui_static()
