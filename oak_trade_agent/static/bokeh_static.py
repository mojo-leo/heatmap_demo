#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import webbrowser
from functools import cached_property
from pathlib import Path

# Third-party modules
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    CustomJS,
    Div,
    HoverTool,
    LogColorMapper,
    LogTicker,
    Slider,
    Spacer,
)
from bokeh.palettes import Viridis256
from bokeh.plotting import figure

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class BokehHeatmapResize:
    """
    This object uses an offline-mode of bokeh to create a heatmap of the
    trade data. To do this we use a CustomJS Top-N slider. So there actually
    is a bit of JavaScript in this class.
    The resulting HTML file size is: 80 KB
    """

    title = "Exporter → Importer heatmap (resize by Top-N countries)"

    @cached_property
    def layout(self):
        df = baci.ranked_oak_df.copy()

        # Log color mappers require strictly positive values.
        # We keep the original `quantity` for data integrity and create a
        # clipped version for coloring so zeros don't break the log transform.
        #
        # Special request: "stop changing color at 1" (i.e. everything below 1
        # uses the same color as 1). We do that by clamping the color-mapper
        # low bound to 1.0 whenever the dataset has any values >= 1.

        positive = df.loc[df["quantity"] > 0, "quantity"]
        min_positive = float(positive.min()) if len(positive) else 1.0
        max_positive = float(positive.max()) if len(positive) else 1.0
        low = 1.0 if max_positive >= 1.0 else min_positive
        df["quantity_color"] = df["quantity"].clip(lower=low)

        # Max N from ranks
        max_n = len(baci.country_ranks)
        initial_n = min(10, max_n)

        # --- UI helpers (mimic the TUI header + slider row) ---
        def _topn_label(n: int) -> str:
            # Using HTML for maximum compatibility across Bokeh versions.
            return f"<label><b>Top N countries</b>: {n}</label>"

        # Build ordered lists of countries by rank (very important)
        exporters_ordered = (
            df[["exporter_name", "exporter_rank"]]
            .drop_duplicates()
            .sort_values("exporter_rank")["exporter_name"]
            .tolist()
        )
        importers_ordered = (
            df[["importer_name", "importer_rank"]]
            .drop_duplicates()
            .sort_values("importer_rank")["importer_name"]
            .tolist()
        )

        # Full dataset (all pairs/rows you have)
        source_all = ColumnDataSource(df)

        # Initial view: only rows within top-N ranks
        mask = (df["exporter_rank"] <= initial_n) & (df["importer_rank"] <= initial_n)
        source_view = ColumnDataSource(df[mask])

        # Color mapper (log scale)
        color_mapper = LogColorMapper(
            palette=Viridis256,
            low=low,
            high=float(df["quantity"].max()),
        )

        # Figure with initial factors = top N
        p = figure(
            title="",
            x_range=exporters_ordered[:initial_n],
            # Bokeh draws the first categorical factor at the bottom of the y-axis.
            # Reverse so "top-ranked" importers appear at the top visually.
            y_range=list(reversed(importers_ordered[:initial_n])),
            x_axis_location="above",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="right",
            sizing_mode="stretch_both",
        )
        # We render our own title `Div` above the plot (closer to the TUI look).
        p.title.visible = False
        p.xaxis.axis_label = "Exporter country"
        p.yaxis.axis_label = "Importer country"

        rect = p.rect(
            x="exporter_name",
            y="importer_name",
            width=1,
            height=1,
            source=source_view,
            line_color=None,
            fill_color={"field": "quantity_color", "transform": color_mapper},
        )

        p.add_tools(
            HoverTool(
                renderers=[rect],
                tooltips=[
                    ("Exporter", "@exporter_name"),
                    ("Importer", "@importer_name"),
                    ("Quantity (tons)", "@quantity{0,0.00}"),
                    ("Value ($)", "@value{0,0.00}"),
                ],
            )
        )

        p.add_layout(
            ColorBar(
                color_mapper=color_mapper,
                title="Quantity (tons, log scale)",
                ticker=LogTicker(),
            ),
            "right",
        )
        p.xaxis.major_label_orientation = 1.0

        # --- Controls row (TUI-like) ---
        title_div = Div(
            text="<div style='font-size:32px;font-weight:700;margin:6px 0 14px 0;'>"
            "Exporter \u2192 Importer heatmap (Top-N by total trade)"
            "</div>",
        )
        n_label = Div(
            text=_topn_label(initial_n),
            styles={"font-size": "16px"},
        )
        hint = Div(
            text="<span style='color:#666;font-size:12px'>X = Exporter \u00b7 Y = Importer</span>",
        )

        slider = Slider(
            start=2,
            end=max_n,
            value=initial_n,
            step=1,
            title="",
            width=340,
            bar_color="#2563eb",
        )

        slider.js_on_change(
            "value",
            CustomJS(
                args=dict(
                    source_all=source_all,
                    source_view=source_view,
                    x_range=p.x_range,
                    y_range=p.y_range,
                    exporters=exporters_ordered,
                    importers=importers_ordered,
                    n_label=n_label,
                ),
                code=self.SLIDER_JS_CODE,
            ),
        )

        controls = row(
            n_label,
            slider,
            Spacer(sizing_mode="stretch_width"),
            hint,
            sizing_mode="stretch_width",
            margin=(0, 0, 10, 0),
        )
        return column(controls, title_div, p, sizing_mode="stretch_both")

    SLIDER_JS_CODE = """
    const N = cb_obj.value;

    // Update the "Top N countries: N" label (TUI-like header row)
    n_label.text = `<label><b>Top N countries</b>: ${N}</label>`;

    // 1) Update the categorical axes to top-N lists
    // (this "resizes" the heatmap)
    const x_factors = exporters.slice(0, N);
    // Bokeh draws first y factor at the bottom; reverse for top-on-top ordering.
    const y_factors = importers.slice(0, N).slice().reverse();
    x_range.factors = x_factors;
    y_range.factors = y_factors;

    // 2) Filter data to those factors so only NxN cells draw
    const data = source_all.data;
    const cols = Object.keys(data);

    const xset = new Set(x_factors);
    const yset = new Set(y_factors);

    const new_data = {};
    cols.forEach(c => new_data[c] = []);

    // assumes exporter_name/importer_name columns exist in source_all
    for (let i = 0; i < data[cols[0]].length; i++) {
        const ex = data['exporter_name'][i];
        const im = data['importer_name'][i];
        if (xset.has(ex) && yset.has(im)) {
            cols.forEach(c => new_data[c].push(data[c][i]));
        }
    }

    source_view.data = new_data;
    source_view.change.emit();
    """

    def __call__(self, open_browser: bool = False) -> Path:
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "bokeh_static.html"
        output_file(output_path, title=self.title)
        save(self.layout)
        print(f"Saved {output_path} — open it in your browser.")
        if open_browser:
            webbrowser.open(f"file://{output_path.absolute()}")
        return output_path


###############################################################################
bokeh_heatmap_resize = BokehHeatmapResize()

if __name__ == "__main__":
    bokeh_heatmap_resize()
