#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Built-in modules
import os
import subprocess
import webbrowser
from functools import cached_property
from pathlib import Path

# Third-party modules
import pandas as pd
import plotly.graph_objects as go
import solara

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class SolaraHeatmap:
    """
    Solara dynamic app (virtual kernel mode via Solara server):

    - Python runs server-side.
    - The browser connects over WebSocket; Solara creates a per-page "virtual kernel"
      (state + execution context) that can survive temporary disconnects.
    - This script defines the Solara Page() component AND provides a __call__ that
      starts `solara run` in a subprocess (so you can launch it like the other classes).
    """

    title = "Exporter → Importer heatmap (Top-N countries by total quantity)"

    @cached_property
    def df(self) -> pd.DataFrame:
        return baci.ranked_oak_df

    @cached_property
    def countries_ordered(self) -> list[str]:
        # Rank 1 = largest; already sorted by BaciDataset.country_ranks
        return baci.country_ranks.index.tolist()

    @cached_property
    def max_n(self) -> int:
        return len(self.countries_ordered)

    @cached_property
    def full_matrix(self) -> pd.DataFrame:
        """
        Build the full NxN quantity matrix once, then slice for Top-N.
        This keeps slider updates fast and deterministic.
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

    def figure_for_n(self, n: int) -> go.Figure:
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

    def __call__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        open_browser: bool = True,
        kernel_cull_timeout: str | None = "5m",
    ) -> None:
        """
        Start Solara using the Solara server (virtual kernels) in a subprocess.

        Notes:
        - `solara run <file.py>` is the standard CLI entrypoint.
        - Virtual kernel lifecycle/culling can be controlled with env vars like
          SOLARA_KERNEL_CULL_TIMEOUT (e.g. "1m", "3h", "2d").
        """
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)

        # Serve *this* file (so code changes immediately reflect when reloaded).
        script_path = Path(__file__).resolve()

        env = os.environ.copy()
        # Ensure the repo root is on PYTHONPATH so `oak_trade_agent` imports work.
        repo_root = Path(__file__).resolve().parents[2]
        env["PYTHONPATH"] = str(repo_root) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )

        # Tell Solara where to bind (env vars are supported; docs also mention --host).
        env["SOLARA_HOST"] = host
        env["PORT"] = str(port)

        if kernel_cull_timeout:
            env["SOLARA_KERNEL_CULL_TIMEOUT"] = str(kernel_cull_timeout)

        url = f"http://{host}:{port}"
        print(f"Starting Solara (virtual kernels) on {url}")
        print("Press Ctrl+C to stop.")

        if open_browser:
            webbrowser.open(url)

        # Use `solara run` to start the Solara server. This will run in "dev mode"
        # by default (auto-reload). Use SOLARA_MODE=production or --production for prod.


###############################################################################
# Make a singleton
solara_heatmap = SolaraHeatmap()


###############################################################################
# Solara entrypoint: Page() component
#
# Solara expects a top-level @solara.component named Page in a script-style app.
# (You can also use layouts/routing, but this matches your other single-page demos.)
top_n = solara.reactive(10)


@solara.component
def Page():
    # Clamp defaults once we know max_n (computed lazily/cached)
    max_n = solara_heatmap.max_n
    if top_n.value < 2 or top_n.value > max_n:
        top_n.set(min(10, max_n))

    with solara.Column():
        solara.Markdown(f"## {solara_heatmap.title}")
        solara.SliderInt(
            label="Top # countries",
            value=top_n,
            min=2,
            max=max_n,
            step=1,
        )
        solara.Markdown(f"**Showing {top_n.value} × {top_n.value} countries**")
        fig = solara_heatmap.figure_for_n(int(top_n.value))
        solara.FigurePlotly(fig)


###############################################################################
# Run the singleton when run as a script
if __name__ == "__main__":
    solara_heatmap()
