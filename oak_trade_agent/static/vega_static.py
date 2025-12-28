#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Built-in modules
import webbrowser
from functools import cached_property
from pathlib import Path

# Third-party modules
import altair

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class VegaHeatmap:
    """
    This object uses vega-lite to create a heatmap of the trade data.
    The result is a standalone HTML file that can be opened in a browser.
    The resulting HTML file size is: 307 KB
    """

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def heatmap(self) -> altair.Chart:
        # Calculate max_n from the dataframe ranks
        max_n = len(baci.country_ranks)
        # Slider parameter for Top N countries to display
        top_n = altair.param(
            name="top_n",
            value=min(10, max_n),
            bind=altair.binding_range(
                min=2, max=max_n, step=1, name="Top # countries: "
            ),
        )
        # The main object that creates the heatmap
        heatmap = (
            altair.Chart(baci.ranked_oak_df)
            .add_params(top_n)
            .transform_filter(
                (altair.datum.exporter_rank <= top_n)
                & (altair.datum.importer_rank <= top_n)
            )
            .mark_rect()
            .encode(
                x=altair.X("exporter_name:N", sort="-x", title="Exporter country"),
                y=altair.Y("importer_name:N", sort="-x", title="Importer country"),
                color=altair.Color("quantity:Q", title="Quantity (tons)"),
                tooltip=[
                    altair.Tooltip("exporter_name:N", title="Exporter"),
                    altair.Tooltip("importer_name:N", title="Importer"),
                    altair.Tooltip("quantity:Q", title="Quantity", format=",.3f"),
                ],
            )
            .properties(
                width=800,
                height=800,
                title=self.title,
            )
        )
        return heatmap

    def __call__(self) -> Path:
        """Create and save a vega-lite heatmap visualization."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_filename = "vega_heatmap_topn.html"
        output_path = output_dir / output_filename
        self.heatmap.save(output_path)
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")
        return output_path


###############################################################################
# Make a singleton
vega_heatmap = VegaHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    vega_heatmap()