# `oak_trade_agent` version 0.1.0

`oak_trade_agent` is a python package to helps answer questions on oak trade statistics based on bilateral Comtrade data. In the starting phase it will provide only a simple visualization of sample data based on oak roundwood and sawnwood (reference number 440791)

Our first objective is simply to compare browser-based plotting methods by generating a heatmap. For this we explore several different strategies, and multiple technologies.

Logo

## Input data

Based on a downloadable zip file with information on trade data from BACI.
The accronym  BACI stands for: Base Pour L’Analyse Du Commerce International.

Details of the dataset here:

    https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html

Basically we end up with a dataframe that looks like this:

DF

## Output graph

A heatmap that is interactive and can be seen in the browser. We want the interface to have a slider that goes from 1 to N, and changes the number of countries that are displayed on the heatmap. Here is a example:

screenshot

## Call

This is how you call the script:

    $ python3 -m oak_trade_agent

And it will populate the `output/` directory in which you will find an HTML file. It will automatically open in your browser.