"""
This script uses vega-lite to create a heatmap of the trade data.
"""

import pandas

from load_baci import load_from_baci_dump, baci_file


def main():
    df = load_from_baci_dump(baci_file, 440791)
