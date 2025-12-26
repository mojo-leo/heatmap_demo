#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
from functools import cached_property

# Third-party modules
import pandas as pd
import plotly.graph_objects as go
from nicegui import ui

# Internal modules
from oak_trade_agent.data.baci_dataset import baci


###############################################################################
class NiceGUIHeatmap:

    title = "Exporter → Importer heatmap (Top-N countries by total quantity)"

    @cached_property
    def df(self) -> pd.DataFrame:
        return baci.ranked_oak_df

    @cached_property
    def countries_ordered(self) -> list[str]:
        # Already sorted by rank (1 = largest)
        return baci.country_ranks.index.tolist()

    @cached_property
    def max_n(self) -> int:
        return len(self.countries_ordered)

    @cached_property
    def full_matrix(self) -> pd.DataFrame:
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

    def _figure_for_n(self, n: int) -> go.Figure:
        countries = self.countries_ordered[:n]
        m = self.full_matrix.loc[countries, countries]

        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=m.to_numpy(),
                    x=countries,
                    y=countries,
                    colorbar=dict(title="Quantity (tons)"),
                    hovertemplate=(
                        "Exporter: %{x}<br>"
                        "Importer: %{y}<br>"
                        "Quantity: %{z:,.3f}<extra></extra>"
                    ),
                )
            ]
        )
        fig.update_layout(
            title=self.title,
            width=900,
            height=900,
            margin=dict(l=120, r=80, t=60, b=120),
            xaxis=dict(title="Exporter country"),
            yaxis=dict(title="Importer country"),
        )
        return fig

    def build(self) -> None:
        default_n = min(10, self.max_n)

        ui.markdown(f"## {self.title}")

        status = ui.label(f"Showing {default_n} × {default_n} countries")

        plot = ui.plotly(self._figure_for_n(default_n))

        def on_change(e) -> None:
            n = int(e.value)
            status.text = f"Showing {n} × {n} countries"
            plot.figure = self._figure_for_n(n)
            plot.update()

        ui.slider(
            min=2,
            max=self.max_n,
            value=default_n,
            step=1,
            on_change=on_change,
        ).props("label label-always")

    def __call__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        self.build()
        ui.run(host=host, port=port)


###############################################################################
# Make a singleton
nicegui_heatmap = NiceGUIHeatmap()

# Run the singleton when run as a script
if __name__ in {"__main__", "__mp_main__"}:
    nicegui_heatmap()
