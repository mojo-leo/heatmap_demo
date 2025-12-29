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
from bokeh.palettes import brewer, interp_palette
from bokeh.plotting import figure

# Internal modules
from ..common import split_thousands
from heatmap_demo import project_url
from heatmap_demo.data.baci_dataset import baci
from heatmap_demo.paths import get_output_dir


###############################################################################
class BokehHeatmapResize:
    """
    This object uses an offline-mode of bokeh to create a heatmap of the
    trade data. To do this we use a CustomJS Top-N slider. So there actually
    is a bit of JavaScript in this class.
    The resulting HTML file size is: 80 KB
    """

    title = "Oak roundwood and sawnwood international commerce heatmap"
    baci_url = "https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html"
    subtitle = "Exporter → Importer quantities from the BACI 2023 dataset"

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
        df["quantity_display"] = df["quantity"].map(split_thousands)
        df["value_display"] = (df["value"] * 1000).map(split_thousands)

        # Max N from ranks
        max_n = len(baci.country_ranks)
        initial_n = min(10, max_n)

        def topn_label(n: int) -> str:
            """Using HTML for maximum compatibility across Bokeh versions.
            Keep the number in a fixed-width box so the slider doesn't shift
            when going from 9 → 10 → 100, etc."""
            return (
                "<label><b>Top N countries displayed</b>: "
                f"<span style='display:inline-block;min-width:3ch;text-align:right'>{n}</span>"
                "</label>"
            )

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

        # Palette: green → cyan → deep blue (close to Altair/Vega-Lite default feel
        # for heatmaps) while keeping a logarithmic color scale.
        gnbu_256 = interp_palette(list(reversed(brewer["GnBu"][9])), 256)

        # Color mapper (log scale)
        color_mapper = LogColorMapper(
            palette=gnbu_256,
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
                    ("Metric tons", "@quantity_display"),
                    ("Value ($)", "@value_display"),
                ],
            )
        )

        p.add_layout(
            ColorBar(
                color_mapper=color_mapper,
                title="Quantity (metric tons, log scale)",
                ticker=LogTicker(),
            ),
            "right",
        )
        p.xaxis.major_label_orientation = 1.0

        # --- Title + Controls ---
        title_div = Div(
            text=(
                "<div style='font-size:24px;font-weight:700;margin:6px 0 8px 0;'>"
                f"{self.title}"
                "</div>"
            )
        )
        n_label = Div(
            text=topn_label(initial_n),
            width=260,
            styles={"font-size": "16px", "white-space": "nowrap"},
        )
        legend = Div(
            text=(
                "<span style='color:#666;font-size:12px'>"
                "Exporter → Importer quantities from the "
                f"<a href='{self.baci_url}' target='_blank' rel='noopener noreferrer'>BACI dataset</a>"
                " (2023)"
                "<br/>"
                "Graph generated with this "
                f"<a href='{project_url}' target='_blank' rel='noopener noreferrer'>python code</a>,"
                "</span>"
            ),
            styles={"text-align": "right"},
        )

        slider = Slider(
            start=2,
            end=max_n,
            value=initial_n,
            step=1,
            title="",
            show_value=False,
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
            Spacer(width=1),
            slider,
            Spacer(sizing_mode="stretch_width"),
            legend,
            sizing_mode="stretch_width",
            margin=(0, 0, 10, 0),
        )
        return column(title_div, controls, p, sizing_mode="stretch_both")

    SLIDER_JS_CODE = """
    const N = cb_obj.value;

    // Update the "Top N countries: N" label (TUI-like header row)
    n_label.text = `<label><b>Top N countries displayed</b>: <span style='display:inline-block;min-width:3ch;text-align:right'>${N}</span></label>`;

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
