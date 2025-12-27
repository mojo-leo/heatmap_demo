#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This code will run client side, in the browser, with a special python runtime
deployed in WebAssembly (WASM). You just need to run this in the current directory:

    $ python -m http.server

And then point your browser to http://localhost:8000.
"""

# Built-in modules
import json
from functools import lru_cache

# Third-party modules
import panel as pn
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.plotting import figure

###############################################################################
# Panel setup
pn.extension(sizing_mode="stretch_width")


###############################################################################
@lru_cache(maxsize=1)
def _load_records() -> list[dict]:
    """Load BACI records from a sibling JSON file (served over HTTP)."""
    # In Pyodide, open_url fetches via the browser.
    from pyodide.http import open_url  # type: ignore

    with open_url("baci_dataset.json") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _countries_and_matrix():
    """Compute ordered country list + full NxN quantity matrix once."""
    records = _load_records()

    # Order countries by total quantity (exports + imports), just like your ranks idea.
    totals: dict[str, float] = {}
    for r in records:
        e = r.get("exporter_name")
        i = r.get("importer_name")
        q = float(r.get("quantity") or 0.0)
        if e:
            totals[e] = totals.get(e, 0.0) + q
        if i:
            totals[i] = totals.get(i, 0.0) + q

    countries = [
        k for k, _ in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    ]
    idx = {c: j for j, c in enumerate(countries)}
    n = len(countries)

    # Build full matrix (rows=importer, cols=exporter)
    mat = [[0.0] * n for _ in range(n)]
    for r in records:
        e = r.get("exporter_name")
        i = r.get("importer_name")
        if e not in idx or i not in idx:
            continue
        q = float(r.get("quantity") or 0.0)
        mat[idx[i]][idx[e]] += q

    return countries, mat


###############################################################################
class PanelWasmHeatmap:
    """Panel-in-Pyodide heatmap with a Top-N slider (client-side Python)."""

    title = "Exporter → Importer heatmap (Top-N by total quantity)"

    def __init__(self):
        countries, _ = _countries_and_matrix()
        self.countries = countries
        self.max_n = max(2, len(countries))

        self.slider = pn.widgets.IntSlider(
            name="Top N countries",
            start=2,
            end=self.max_n,
            step=1,
            value=min(10, self.max_n),
        )

        self.source = ColumnDataSource(data=dict(x=[], y=[], q=[]))

        self.mapper = LinearColorMapper(palette="Viridis256", low=0.0, high=1.0)

        self.fig = figure(
            x_range=[],
            y_range=[],
            width=900,
            height=900,
            title=self.title,
            toolbar_location="above",
            tools="pan,wheel_zoom,reset,save",
        )
        self.fig.xaxis.axis_label = "Exporter country"
        self.fig.yaxis.axis_label = "Importer country"
        self.fig.xaxis.major_label_orientation = 0.785398  # 45°

        self.fig.rect(
            x="x",
            y="y",
            width=1,
            height=1,
            source=self.source,
            line_color=None,
            fill_color={"field": "q", "transform": self.mapper},
        )

        color_bar = ColorBar(
            color_mapper=self.mapper,
            ticker=BasicTicker(desired_num_ticks=8),
            label_standoff=8,
            border_line_color=None,
            location=(0, 0),
        )
        self.fig.add_layout(color_bar, "right")

        # Wire slider
        self.slider.param.watch(lambda *_: self._update(), "value")
        self._update()

        self.app = pn.Column(
            pn.pane.Markdown("**X-axis = Exporter · Y-axis = Importer**"),
            self.slider,
            self.fig,
        )

    def _update(self):
        countries, mat = _countries_and_matrix()
        n = int(self.slider.value)
        names = countries[:n]

        xs, ys, qs = [], [], []
        vmax = 0.0
        for yi in range(n):
            for xi in range(n):
                v = float(mat[yi][xi])
                vmax = max(vmax, v)
                xs.append(names[xi])
                ys.append(names[yi])
                qs.append(v)

        # Update axis ranges + data
        self.fig.x_range.factors = names
        self.fig.y_range.factors = list(reversed(names))
        self.source.data = dict(x=xs, y=ys, q=qs)

        # Keep 0 white-ish by starting low at 0
        self.mapper.low = 0.0
        self.mapper.high = vmax if vmax > 0 else 1.0


###############################################################################
# Make a singleton and serve it into a DOM node with id="app"
wasm_heatmap = PanelWasmHeatmap()
wasm_heatmap.app.servable(target="app")
