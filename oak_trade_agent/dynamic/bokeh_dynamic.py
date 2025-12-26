#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Built-in modules
import webbrowser
from functools import cached_property

# Third-party modules
import pandas as pd
from bokeh.layouts import column
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    HoverTool,
    LinearColorMapper,
    Slider,
)
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.transform import transform

# Internal modules
from oak_trade_agent.data.baci_dataset import baci


###############################################################################
class BokehServerHeatmap:
    """
    Pure Bokeh *embedded server* app:
    - Run this file with `python .../bokeh_dynamic.py`
    - Starts a Bokeh server programmatically (no `bokeh serve` command needed)
    - Slider filters to Top-N countries
    """

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def df(self) -> pd.DataFrame:
        return baci.ranked_oak_df

    @cached_property
    def max_n(self) -> int:
        return int(max(self.df["exporter_rank"].max(), self.df["importer_rank"].max()))

    def _filtered_df(self, top_n: int) -> pd.DataFrame:
        return self.df[
            (self.df["exporter_rank"] <= top_n) & (self.df["importer_rank"] <= top_n)
        ]

    def make_document(self, doc) -> None:
        default_n = min(10, self.max_n)
        df0 = self._filtered_df(default_n)

        source = ColumnDataSource(df0)

        mapper = LinearColorMapper(
            palette="Viridis256",
            low=float(df0["quantity"].min()),
            high=float(df0["quantity"].max()),
        )

        p = figure(
            title=self.title,
            x_range=sorted(df0["exporter_name"].unique().tolist()),
            y_range=sorted(df0["importer_name"].unique().tolist()),
            x_axis_location="above",
            width=800,
            height=800,
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="right",
        )

        # Axis labels and tick orientation
        p.xaxis.axis_label = "Exporter country"
        p.yaxis.axis_label = "Importer country"
        p.xaxis.major_label_orientation = 3.14159 / 4  # 45 degrees

        p.rect(
            x="exporter_name",
            y="importer_name",
            width=1,
            height=1,
            source=source,
            fill_color=transform("quantity", mapper),
            line_color=None,
        )

        p.add_tools(
            HoverTool(
                tooltips=[
                    ("Exporter", "@exporter_name"),
                    ("Importer", "@importer_name"),
                    ("Quantity", "@quantity{0,0.000}"),
                ]
            )
        )

        p.add_layout(ColorBar(color_mapper=mapper, title="Quantity (tons)"), "right")

        slider = Slider(
            title="Top N countries",
            start=2,
            end=self.max_n,
            step=1,
            value=default_n,
        )

        def on_slider_change(attr, old, new):
            df_new = self._filtered_df(int(new))
            source.data = ColumnDataSource.from_df(df_new)

            p.x_range.factors = sorted(df_new["exporter_name"].unique().tolist())
            p.y_range.factors = sorted(df_new["importer_name"].unique().tolist())

            mapper.low = float(df_new["quantity"].min())
            mapper.high = float(df_new["quantity"].max())

        slider.on_change("value", on_slider_change)

        doc.add_root(column(slider, p))

    def __call__(self, host: str = "127.0.0.1", port: int = 5006) -> None:
        """
        Start the Bokeh server programmatically and open a browser tab.
        """
        url = f"http://{host}:{port}/"
        print(f"Starting Bokeh server at {url}")
        print("Press Ctrl+C to stop.")

        server = Server(
            {"/": self.make_document},
            address=host,
            port=port,
            allow_websocket_origin=[f"{host}:{port}"],
            num_procs=1,
        )
        server.start()

        server.io_loop.add_callback(server.show, "/")
        try:
            server.io_loop.start()
        except KeyboardInterrupt:
            pass


###############################################################################
# Make a singleton
bokeh_server_heatmap = BokehServerHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    bokeh_server_heatmap()
