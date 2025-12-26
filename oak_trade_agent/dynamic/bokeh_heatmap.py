#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses Bokeh Server to create an interactive heatmap of the trade data.
"""

# Built-in modules
from functools import cached_property

# Third-party modules
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    HoverTool,
    LinearColorMapper,
    Slider,
)
from bokeh.plotting import figure

# Internal modules
from oak_trade_agent.data.baci_dataset import baci


###############################################################################
class BokehServerHeatmap:
    """Creates a Bokeh Server interactive heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def data_prep(self) -> dict:
        """Prepare and cache the data for the heatmap."""
        df = baci.ranked_oak_df
        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))

        # Create pivot table for heatmap
        # Aggregate quantity by exporter_name and importer_name
        pivot_df = (
            df.groupby(["exporter_name", "importer_name"])["quantity"]
            .sum()
            .reset_index()
        )

        # Create list of unique countries sorted by rank
        exporter_totals = (
            df.groupby("exporter_name")["quantity"].sum().sort_values(ascending=False)
        )
        importer_totals = (
            df.groupby("importer_name")["quantity"].sum().sort_values(ascending=False)
        )
        # Sort by total trade (exports + imports)
        country_totals = exporter_totals.add(importer_totals, fill_value=0)
        country_totals = country_totals.sort_values(ascending=False)
        sorted_countries = country_totals.index.tolist()

        return {
            "pivot_df": pivot_df,
            "sorted_countries": sorted_countries,
            "max_n": max_n,
        }

    def create_heatmap_data(self, top_n: int) -> dict:
        """Create heatmap data for the given top_n value."""
        data = self.data_prep
        sorted_countries = data["sorted_countries"]
        pivot_df = data["pivot_df"]

        top_countries = sorted_countries[:top_n]
        filtered_df = pivot_df[
            pivot_df["exporter_name"].isin(top_countries)
            & pivot_df["importer_name"].isin(top_countries)
        ]

        # Create pivot matrix
        heatmap_matrix = filtered_df.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            fill_value=0,
        )

        # Reorder rows and columns to match sorted order
        heatmap_matrix = heatmap_matrix.reindex(
            index=[c for c in sorted_countries if c in heatmap_matrix.index],
            columns=[c for c in sorted_countries if c in heatmap_matrix.columns],
        )

        # Prepare data for Bokeh
        exporter_names = heatmap_matrix.columns.tolist()
        importer_names = heatmap_matrix.index.tolist()

        # Create arrays for x, y coordinates
        x_coords = []
        y_coords = []
        quantities = []
        exporter_labels = []
        importer_labels = []

        for i, importer in enumerate(importer_names):
            for j, exporter in enumerate(exporter_names):
                x_coords.append(j)
                y_coords.append(i)
                quantities.append(heatmap_matrix.loc[importer, exporter])
                exporter_labels.append(exporter)
                importer_labels.append(importer)

        return {
            "x": x_coords,
            "y": y_coords,
            "quantity": quantities,
            "exporter": exporter_labels,
            "importer": importer_labels,
            "exporter_names": exporter_names,
            "importer_names": importer_names,
        }

    def setup_document(self) -> None:
        """Set up the Bokeh document with interactive heatmap and slider."""
        data = self.data_prep
        max_n = data["max_n"]
        default_top_n = min(10, max_n)

        # Create initial heatmap data
        initial_data = self.create_heatmap_data(default_top_n)

        # Create ColumnDataSource
        source = ColumnDataSource(data=initial_data)

        # Create color mapper
        min_qty = min(initial_data["quantity"]) if initial_data["quantity"] else 0
        max_qty = max(initial_data["quantity"]) if initial_data["quantity"] else 1
        color_mapper = LinearColorMapper(
            palette="Viridis256", low=min_qty, high=max_qty
        )

        # Create figure
        p = figure(
            width=800,
            height=800,
            title=f"{self.title} (Top {default_top_n} countries)",
            x_range=initial_data["exporter_names"],
            y_range=list(reversed(initial_data["importer_names"])),
            tools="pan,box_zoom,wheel_zoom,reset,save",
            toolbar_location="above",
        )

        # Create rectangles for heatmap
        p.rect(
            x="x",
            y="y",
            width=0.95,
            height=0.95,
            source=source,
            fill_color={"field": "quantity", "transform": color_mapper},
            line_color=None,
        )

        # Add hover tool
        hover = HoverTool(
            tooltips=[
                ("Exporter", "@exporter"),
                ("Importer", "@importer"),
                ("Quantity", "@quantity{0,0.000} tons"),
            ]
        )
        p.add_tools(hover)

        # Add color bar
        color_bar = ColorBar(
            color_mapper=color_mapper,
            label_standoff=12,
            border_line_color=None,
            location=(0, 0),
            title="Quantity (tons)",
        )
        p.add_layout(color_bar, "right")

        # Set axis labels
        p.xaxis.axis_label = "Exporter country"
        p.yaxis.axis_label = "Importer country"
        p.xaxis.major_label_orientation = 3.14159 / 4  # 45 degrees

        # Create slider for Top N
        slider = Slider(
            start=2,
            end=max_n,
            value=default_top_n,
            step=1,
            title="Top # countries:",
            width=600,
        )

        # Define callback to update heatmap based on slider
        def update_heatmap(attr, old, new):
            """Update the heatmap when the slider value changes."""
            top_n = slider.value
            new_data = self.create_heatmap_data(top_n)

            # Update source data
            source.data = {
                "x": new_data["x"],
                "y": new_data["y"],
                "quantity": new_data["quantity"],
                "exporter": new_data["exporter"],
                "importer": new_data["importer"],
            }

            # Update axis ranges
            p.x_range.factors = new_data["exporter_names"]
            p.y_range.factors = list(reversed(new_data["importer_names"]))

            # Update color mapper range
            if new_data["quantity"]:
                min_qty = min(new_data["quantity"])
                max_qty = max(new_data["quantity"])
                color_mapper.low = min_qty
                color_mapper.high = max_qty

            # Update title
            p.title.text = f"{self.title} (Top {top_n} countries)"

        slider.on_change("value", update_heatmap)

        # Combine plot and slider
        layout = column(slider, p)

        # Add to document
        doc = curdoc()
        doc.add_root(layout)
        doc.title = "Oak Trade Heatmap"

    def __call__(self, port: int = 5006, host: str = "127.0.0.1") -> None:
        """Run the Bokeh server."""
        from bokeh.server.server import Server
        from bokeh.application import Application
        from bokeh.application.handlers.function import FunctionHandler

        print(f"Starting Bokeh server on http://{host}:{port}")
        print("Press Ctrl+C to stop the server.")

        # Create application
        app = Application(FunctionHandler(self.setup_document))

        # Create and start server
        server = Server({"/": app}, port=port, address=host)
        server.start()

        # Open browser
        server.io_loop.add_callback(server.show, "/")

        try:
            server.io_loop.start()
        except KeyboardInterrupt:
            print("\nStopping server...")


###############################################################################
# Make a singleton
bokeh_server_heatmap = BokehServerHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    bokeh_server_heatmap()

