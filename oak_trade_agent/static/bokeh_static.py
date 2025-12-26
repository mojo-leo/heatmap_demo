#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import webbrowser
from functools import cached_property

from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import (
    ColumnDataSource, CustomJS, Slider,
    LinearColorMapper, ColorBar,
)
from bokeh.plotting import figure
from bokeh.palettes import Viridis256

from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


class BokehHeatmapResize:
    """
    This object uses an offline-mode of bokeh to create a heatmap of the
    trade data. To do this we use a CustomJS Top-N slider. So there actually
    is a bit of javascript in this class.
    """

    title = "Exporter → Importer heatmap (resize by Top-N countries)"

    @cached_property
    def layout(self):
        df = baci.ranked_oak_df.copy()

        # Max N from ranks
        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))
        initial_n = min(10, max_n)

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

        # Color mapper
        color_mapper = LinearColorMapper(
            palette=Viridis256,
            low=float(df["quantity"].min()),
            high=float(df["quantity"].max()),
        )

        # Figure with initial factors = top N
        p = figure(
            title=self.title,
            x_range=exporters_ordered[:initial_n],
            y_range=importers_ordered[:initial_n],
            x_axis_location="above",
            width=800,
            height=800,
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="right",
        )

        p.rect(
            x="exporter_name",
            y="importer_name",
            width=1,
            height=1,
            source=source_view,
            line_color=None,
            fill_color={"field": "quantity", "transform": color_mapper},
        )

        p.add_layout(ColorBar(color_mapper=color_mapper, title="Quantity (tons)"), "right")
        p.xaxis.major_label_orientation = 1.0

        slider = Slider(start=2, end=max_n, value=initial_n, step=1, title="Top # countries")

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
                ),
                code="""
                const N = cb_obj.value;

                // 1) Update the categorical axes to top-N lists (this "resizes" the heatmap)
                const x_factors = exporters.slice(0, N);
                const y_factors = importers.slice(0, N);
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
            )
        )

        return column(slider, p)

    def __call__(self) -> None:
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / "bokeh_heatmap_resize_topn.html"
        output_file(output_path, title=self.title)
        save(self.layout)

        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")


bokeh_heatmap_resize = BokehHeatmapResize()

if __name__ == "__main__":
    bokeh_heatmap_resize()