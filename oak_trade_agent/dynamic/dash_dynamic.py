#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Built-in modules
from functools import cached_property

# Third-party modules
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

# Internal modules
from oak_trade_agent.data.baci_dataset import baci


###############################################################################
class DashHeatmap:
    """
    Dash app:
    - Slider controls Top-N countries
    - Plotly Heatmap requires a dense 2D grid -> we build the full pivot once
    - Callback slices rows/cols for N and returns a new figure
    """

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
        """
        Full NxN pivot matrix (rows=importers, cols=exporters).
        Missing pairs filled with 0 so any slice is fully populated.
        """
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

    def _register_callbacks(self, app: Dash) -> None:
        @app.callback(
            Output("heatmap", "figure"),
            Output("status", "children"),
            Input("top_n", "value"),
        )
        def _update(top_n: int):
            n = int(top_n)
            return self._figure_for_n(n), f"Showing {n} × {n} countries"

    @cached_property
    def app(self) -> Dash:
        app = Dash(__name__)

        default_n = min(10, self.max_n)

        app.layout = html.Div(
            [
                html.H3(self.title),
                dcc.Slider(
                    id="top_n",
                    min=2,
                    max=self.max_n,
                    step=1,
                    value=default_n,
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
                html.Div(
                    id="status", style={"marginTop": "8px", "marginBottom": "8px"}
                ),
                dcc.Graph(id="heatmap", figure=self._figure_for_n(default_n)),
            ],
            style={"maxWidth": "1100px", "margin": "0 auto"},
        )

        self._register_callbacks(app)
        return app

    def __call__(
        self, host: str = "127.0.0.1", port: int = 8050, debug: bool = True
    ) -> None:
        self.app.run(host=host, port=port, debug=debug)


###############################################################################
# Make a singleton
dash_heatmap = DashHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    dash_heatmap()
