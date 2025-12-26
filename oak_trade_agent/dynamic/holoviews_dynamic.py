#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses HoloViews Server to create an interactive heatmap of the trade data.
"""

# Built-in modules
from functools import cached_property

# Third-party modules
import holoviews as hv
import panel as pn

# Internal modules
from oak_trade_agent.data.baci_dataset import baci

# Set the backend for HoloViews
hv.extension("bokeh")
pn.extension()


###############################################################################
class HoloviewsServerHeatmap:
    """Creates a HoloViews Server interactive heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def heatmap(self) -> pn.Column:
        """Create the holoviews heatmap visualization with interactive slider."""
        # Calculate max_n from the dataframe ranks
        df = baci.ranked_oak_df
        max_n = len(baci.country_ranks)
        default_top_n = min(10, max_n)

        # Create a function that generates the heatmap based on top_n
        def create_heatmap(top_n: int) -> hv.HeatMap:
            """Create heatmap filtered by top_n countries."""
            filtered_df = df[
                (df["exporter_rank"] <= top_n) & (df["importer_rank"] <= top_n)
            ]
            # Create the heatmap
            heatmap = hv.HeatMap(
                filtered_df,
                kdims=["exporter_name", "importer_name"],
                vdims=["quantity"],
            )
            # Sort by exporter and importer names
            heatmap = heatmap.sort(["exporter_name", "importer_name"])
            # Apply styling
            heatmap = heatmap.opts(
                width=800,
                height=800,
                title=self.title,
                xlabel="Exporter country",
                ylabel="Importer country",
                colorbar=True,
                cmap="Viridis",
                tools=["hover"],
                xrotation=45,
                yrotation=0,
            )
            return heatmap

        # Create a Panel widget for the slider
        top_n_slider = pn.widgets.IntSlider(
            name="Top # countries:",
            start=2,
            end=max_n,
            step=1,
            value=default_top_n,
        )

        # Create a dynamic map that updates with the slider
        # Use pn.bind to connect the widget to the function
        dmap = pn.bind(create_heatmap, top_n=top_n_slider)

        # Combine the slider and heatmap in a Panel layout
        return pn.Column(top_n_slider, dmap)

    @cached_property
    def app(self) -> pn.Column:
        return self.heatmap

    def __call__(self, port: int = 5006, host: str = "localhost") -> None:
        """Run the HoloViews server using Panel."""
        self.app.show(port=port, address=host)


###############################################################################
# Make a singleton
holoviews_server_heatmap = HoloviewsServerHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    holoviews_server_heatmap()
