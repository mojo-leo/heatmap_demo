#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Internal modules
from oak_trade_agent.with_js.template import TemplateHTML


###############################################################################
class ObservablePlot(TemplateHTML):
    """
    A class that embeds BACI JSON data into an Observable Plot HTML template by
    replacing the `__EMBEDDED_DATA__` placeholder.
    """

    template_name = "observable.html"


###############################################################################
observable_plot = ObservablePlot()
if __name__ == "__main__":
    observable_plot()
