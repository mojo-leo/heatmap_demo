# `oak_trade_agent` version 0.1.0

`oak_trade_agent` is a python package to helps answer questions on oak trade statistics based on bilateral Comtrade data. In the starting phase it will provide only a simple visualization of sample data based on oak roundwood and sawnwood (reference number 440791)

## Input data

Based on a downloadable zip file with information on trade data from BACI.
The accronym  BACI stands for: Base Pour L’Analyse Du Commerce International.

Details of the dataset here:

    https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html

## Output graph

A graph that is interactive and can be seen in the browser.

## Call

This is how you call the script:

    $ python3 -m oak_trade_agent

And it will populate the `output/` directory in which you will find an HTML file. It will automatically open in your browser.