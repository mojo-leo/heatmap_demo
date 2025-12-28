#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
from functools import cached_property

# Third-party modules
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Internal modules
from heatmap_demo.data.baci_dataset import baci


###############################################################################
class StreamlitHeatmap:

    title = "Exporter → Importer heatmap (Top-N countries by total quantity)"

    @cached_property
    def df(self) -> pd.DataFrame:
        # Streamlit reruns the script, but cached_property still helps
        return baci.ranked_oak_df

    @cached_property
    def countries_ordered(self) -> list[str]:
        # Already sorted: rank 1 = largest
        return baci.country_ranks.index.tolist()

    @cached_property
    def max_n(self) -> int:
        return len(self.countries_ordered)

    @st.cache_data(show_spinner=False)
    def full_matrix(self) -> pd.DataFrame:
        """Build the FULL NxN pivot matrix ONCE. Cached across reruns."""
        countries = self.countries_ordered
        sub = self.df[["exporter_name", "importer_name", "quantity"]]

        mat = sub.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            aggfunc="sum",
            fill_value=0.0,
        ).reindex(index=countries, columns=countries, fill_value=0.0)
        return mat

    def slice_for_n(self, n: int) -> tuple[list[str], list[str], list[list[float]]]:
        countries = self.countries_ordered[:n]
        mat_n = self.full_matrix().loc[countries, countries]
        return countries, countries, mat_n.to_numpy().tolist()

    def render(self) -> None:
        """Render the Streamlit UI (called on every rerun)."""
        st.set_page_config(page_title=self.title, layout="wide")
        st.title(self.title)

        n = st.slider(
            "Top N countries",
            min_value=2,
            max_value=self.max_n,
            value=min(10, self.max_n),
            step=1,
        )

        x, y, z = self.slice_for_n(n)

        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=z,
                    x=x,
                    y=y,
                    colorbar=dict(title="Quantity (tons)"),
                    hovertemplate=(
                        "Exporter: %{x}<br>"
                        "Importer: %{y}<br>"
                        "Quantity: %{z:,.3f}<extra></extra>"
                    ),
                )
            ],
            layout=go.Layout(
                width=900,
                height=900,
                margin=dict(l=120, r=80, t=80, b=120),
                xaxis=dict(title="Exporter country"),
                yaxis=dict(title="Importer country"),
            ),
        )

        st.plotly_chart(fig, use_container_width=False)

        st.caption(f"Showing {n} × {n} countries")

    def __call__(self) -> None:
        self.render()


###############################################################################
# Make a singleton
streamlit_heatmap = StreamlitHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    streamlit_heatmap()
