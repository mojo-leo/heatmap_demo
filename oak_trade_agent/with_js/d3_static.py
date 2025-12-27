#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import webbrowser
from pathlib import Path

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class D3Static:
    """
    A class that embeds BACI JSON data into a D3 HTML template by replacing the
    `__EMBEDDED_DATA__` placeholder.
    """

    template_name = "d3_static.html"

    @property
    def body(self) -> str:
        html_template_path = Path(__file__).parent / self.template_name
        html_content = Path(html_template_path).read_text()
        return html_content.replace("__EMBEDDED_DATA__", baci.json)

    def __call__(self) -> Path:
        output_path = get_output_dir() / self.template_name
        output_path.write_text(self.body)
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")
        return output_path


###############################################################################
d3_static = D3Static()
if __name__ == "__main__":
    d3_static()
