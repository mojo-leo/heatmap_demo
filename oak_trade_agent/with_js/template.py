#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import webbrowser
from pathlib import Path

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class TemplateHTML:
    """
    Base class for embedding BACI JSON data into HTML templates by replacing the
    `__EMBEDDED_DATA__` placeholder.
    """

    @property
    def template_name(self) -> NotImplementedError:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def body(self) -> str:
        html_template_path = Path(__file__).parent / self.template_name
        html_content = Path(html_template_path).read_text()
        # Wrap the base64 string in quotes to make it a valid JavaScript string literal
        return html_content.replace("__EMBEDDED_DATA__", f'"{baci.json_gzip_base64}"')

    def __call__(self, open_browser: bool = False) -> Path:
        output_path = get_output_dir() / self.template_name
        output_path.write_text(self.body)
        print(f"Saved {output_path} — open it in your browser.")
        if open_browser:
            webbrowser.open(f"file://{output_path.absolute()}")
        return output_path
