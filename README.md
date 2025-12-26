# `oak_trade_agent` version 0.1.0

`oak_trade_agent` is a python package to helps answer questions on oak trade statistics based on bilateral Comtrade data. In the starting phase it will provide only a simple visualization of sample data based on oak roundwood and sawnwood (reference number 440791)

Our first objective is simply to compare browser-based plotting methods by generating a heatmap. For this we explore several different strategies, and multiple technologies.

<p align="center">
<img height="128" src="docs/logo.png?raw=true" alt="Logo showing a stack of wood">
</p>


## Input data

Based on a downloadable zip file with information on trade data from BACI.
The acronym  BACI stands for: "Base Pour L’Analyse Du Commerce International".

Details of the dataset here:

    https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html

Basically we end up with a dataframe that looks like this:

| year   | exporter   | importer   | product   | value      | quantity   | exporter_name   | importer_name   | exporter_rank   | importer_rank   |
|:-------|:-----------|:-----------|:----------|:-----------|:-----------|:----------------|:----------------|:----------------|:----------------|
| 2023   | 842        | 156        | 440791    | 270331.285 | 170800.681 | USA             | China           | 1               | 2               |
| 2023   | 842        | 191        | 440791    | 28.202     | 12.332     | USA             | Croatia         | 1               | 3               |
| 2023   | 842        | 251        | 440791    | 4325.4     | 2818.865   | USA             | France          | 1               | 4               |
| 2023   | 842        | 276        | 440791    | 12428.872  | 9670.643   | USA             | Germany         | 1               | 5               |
| ...    | ...        | ...        | ...       | ...        | ...        | ...             | ...             | ...             | ...             |
| 2023   | 516        | 24         | 440791    | 0.751      | 0.182      | Namibia         | Angola          | 132             | 122             |
| 2023   | 231        | 276        | 440791    | 5.851      | 6.028      | Ethiopia        | Germany         | 138             | 5               |
| 2023   | 231        | 233        | 440791    | 6.376      | 1.225      | Ethiopia        | Estonia         | 138             | 40              |
| 2023   | 218        | 372        | 440791    | 0.107      | 0.009      | Ecuador         | Ireland         | 149             | 47              |

    from oak_trade_agent.data.baci_dataset import baci
    df = baci.ranked_oak_df
    preview = pandas.concat([df.head(), df.tail()])
    print(preview.to_markdown())

## Output graph

A heatmap that is interactive and can be seen in the browser. We want the interface to have a slider that goes from 1 to N, and changes the number of countries that are displayed on the heatmap. Here is a example:

<p align="center">
<img src="docs/vega_screenshot.png?raw=true" alt="Logo showing a stack of wood">
</p>

## Call

To generate the heapmap shown above, this is how you call the script:

    $ python3 -m oak_trade_agent

And it will populate the `output/` directory in which you will find an HTML file. It will automatically open in your browser.

## Technologies

Several approches can be used to generate an interactive animated heatmap.

### Static in Python

The first idea is to write all the code in python while avoiding javascript and create a standalone HTML file that can be served in a static fashion. Not many solutions exist, the main one is `altair` (`vega_lite`). By being hacky it's possible to use `plotly`, `holoviews` or even `bokeh` to obtain a similar result, but these tests have not been working very well.

- [x] `oak_trade_agent.static.vega_static.py`
- [ ] `oak_trade_agent.static.holoviews_static.py`
- [ ] `oak_trade_agent.static.plotly_static.py`
- [x] `oak_trade_agent.static.bokeh_static.py`

### Dynamic in Python

Another approach is to write all the code in python and have a dynamic webapp that serves the content to the browser. This server can also communicate with the browser and answer requests (such as filtering the dataframe) as the user interacts with the dashboard.

- [ ] `oak_trade_agent.dynamic.voila_heatmap.py`
- [ ] `oak_trade_agent.dynamic.streamlit_heatmap.py`
- [ ] `oak_trade_agent.dynamic.shiny_heatmap.py`
- [ ] `oak_trade_agent.dynamic.holoviews_heatmap.py`
- [ ] `oak_trade_agent.dynamic.dash_heatmap.py`
- [ ] `oak_trade_agent.dynamic.d3blocks_heatmap.py`
- [ ] `oak_trade_agent.dynamic.bokeh_heatmap.py`

Links:

* https://hvplot.holoviz.org/en/docs/latest/index.html

### Static in Javascript

The third approach is 


### Dynamic in Javascript


The fourth approach is 
