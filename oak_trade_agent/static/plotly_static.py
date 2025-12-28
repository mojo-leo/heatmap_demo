#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import webbrowser
from functools import cached_property
from pathlib import Path

# Third-party modules
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class PlotlyHeatmapOffline:
    """
    Standalone Plotly HTML heatmap with a Top-N slider (no server).
    This is "offline" in the sense of no server, but it precomputes every N.
    If max_n is large, the HTML can get big.
    To reduce size, change the loop to only generate a subset
    (e.g., steps of 1 up to 30, then steps of 5/10), or cap max_n.
    The resulting HTML file size is: 12.2 MB
    """

    title = "Exporter → Importer heatmap (resize by Top-N countries)"

    def _ordered_lists(self, df: pd.DataFrame):
        exporters = (
            df[["exporter_name", "exporter_rank"]]
            .drop_duplicates()
            .sort_values("exporter_rank")["exporter_name"]
            .tolist()
        )
        importers = (
            df[["importer_name", "importer_rank"]]
            .drop_duplicates()
            .sort_values("importer_rank")["importer_name"]
            .tolist()
        )
        return exporters, importers

    def _matrix_for_n(
        self, df: pd.DataFrame, exporters: list[str], importers: list[str], n: int
    ):
        x = exporters[:n]
        y = importers[:n]

        # Filter to top-N x top-N
        sub = df[(df["exporter_name"].isin(x)) & (df["importer_name"].isin(y))][
            ["exporter_name", "importer_name", "quantity"]
        ]

        # Pivot to full NxN matrix and fill missing with 0
        mat = (
            sub.pivot_table(
                index="importer_name",
                columns="exporter_name",
                values="quantity",
                aggfunc="sum",
                fill_value=0.0,
            )
            .reindex(index=y, columns=x, fill_value=0.0)
            .to_numpy()
        )
        return x, y, mat

    @cached_property
    def fig(self) -> go.Figure:
        df = baci.ranked_oak_df.copy()

        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))
        min_n = 2
        initial_n = min(10, max_n)

        exporters, importers = self._ordered_lists(df)

        # Precompute matrices for each N (offline slider swaps frames)
        frames = []
        global_min = float(df["quantity"].min())
        global_max = float(df["quantity"].max())

        # Initial trace data
        x0, y0, z0 = self._matrix_for_n(df, exporters, importers, initial_n)

        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=z0,
                    x=x0,
                    y=y0,
                    colorbar=dict(title="Quantity (tons)"),
                    zmin=global_min,
                    zmax=global_max,
                    hovertemplate=(
                        "Exporter: %{x}<br>"
                        "Importer: %{y}<br>"
                        "Quantity: %{z:,.3f}<extra></extra>"
                    ),
                )
            ],
            layout=go.Layout(
                title=self.title,
                width=900,
                height=900,
                xaxis=dict(title="Exporter country"),
                yaxis=dict(title="Importer country"),
                margin=dict(l=120, r=80, t=80, b=120),
            ),
        )

        for n in range(min_n, max_n + 1):
            x, y, z = self._matrix_for_n(df, exporters, importers, n)
            frames.append(
                go.Frame(
                    name=str(n),
                    data=[
                        go.Heatmap(
                            z=z,
                            x=x,
                            y=y,
                            zmin=global_min,
                            zmax=global_max,
                        )
                    ],
                    layout=go.Layout(
                        xaxis=dict(categoryorder="array", categoryarray=x),
                        yaxis=dict(categoryorder="array", categoryarray=y),
                    ),
                )
            )

        fig.frames = frames

        # Slider steps: jump to frame "n"
        steps = []
        for n in range(min_n, max_n + 1):
            steps.append(
                dict(
                    method="animate",
                    label=str(n),
                    args=[
                        [str(n)],
                        dict(
                            mode="immediate",
                            frame=dict(duration=0, redraw=True),
                            transition=dict(duration=0),
                        ),
                    ],
                )
            )

        fig.update_layout(
            sliders=[
                dict(
                    active=initial_n - min_n,
                    currentvalue=dict(prefix="Top # countries: "),
                    pad=dict(t=30),
                    steps=steps,
                )
            ]
        )

        return fig

    def __call__(self) -> Path:
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "plotly_static.html"
        self.fig.write_html(
            output_path,
            include_plotlyjs="cdn",  # set True to fully embed JS offline
            full_html=True,
            auto_open=False,
        )
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")
        return output_path


###############################################################################
# Make a singleton
plotly_heatmap_offline = PlotlyHeatmapOffline()

if __name__ == "__main__":
    plotly_heatmap_offline()