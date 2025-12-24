# `oak_trade_agent` version 0.1.0

`oak_trade_agent` is a python package to helps answer questions on oak trade statistics based on bilateral Comtrade data. In the starting phase it will provide only a simple visualization of sample data based on oak roundwood and sawnwood (reference number 440791)

## Input data

Based on a downloadable zip file with information on trade data from BACI.
The accronym stands for BACI: Base Pour L’Analyse Du Commerce International.

## Output graph

A graph that is interactive and can be seen in the browser.

## Call

This is how you call the script:

    $ ./oak_trade_agent/vega_heatmap.py

And it will populate the `output/` directory in which you will find an HTML file.