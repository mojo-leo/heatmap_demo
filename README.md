# `heatmap_demo` version 1.0.0

`heatmap_demo` is a python package to help answer questions on oak trade statistics based on bilateral Comtrade data. In the starting phase it will provide only a simple visualization of sample data based on oak roundwood and sawnwood (reference number 440791)

Our first objective is simply to compare browser-based plotting methods by generating a heatmap. For this, we explore several different strategies and multiple technologies.

<p align="center">
<img height="256" src="docs/logo.png?raw=true" alt="Logo showing a stack of wood and a heatmap">
</p>

## Input data

Based on a downloadable zip file with information on trade data from BACI.
The acronym BACI stands for: "Base Pour L’Analyse Du Commerce International".

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

    from heatmap_demo.data.baci_dataset import baci
    df = baci.ranked_oak_df
    preview = pandas.concat([df.head(), df.tail()])
    print(preview.to_markdown())

## Output graph

A heatmap that is interactive and can be seen in the browser. We want the interface to have a slider that goes from 1 to N, and changes the number of countries that are displayed on the heatmap. Here is an example:

<p align="center">
<a href="https://mojo-leo.github.io/heatmap_demo/output/bokeh_static.html">
<img src="docs/bokeh_screenshot.png?raw=true" alt="Screenshot of the bokeh_static method">
</a>
</p>

## Call

To generate the heapmap shown above, this is how you call the script:

    $ python3 -m heatmap_demo

And it will populate the `output/` directory in which you will find an HTML file. It will automatically open in your browser.

## Technologies

Several approaches can be used to generate an interactive animated heatmap. See:

https://github.com/hal9ai/awesome-dataviz

### 1) Static in Python

The first idea is to write all the code in python while avoiding JavaScript and create a standalone HTML file that can be served in a static fashion. Not many solutions exist, the main one is `altair` (`vega_lite`). By being hacky it's possible to use `holoviews` or even `plotly` to obtain a similar result, but these tests produce huge file sizes. With a bit of in-line javascript we can even do a hack with `bokeh` and get a small file size. Honorable mention for `d3blocks` also though it doesn't provide a slider.

- [x] `heatmap_demo/static/vega_static.py` (with cdn)
- [x] `heatmap_demo/static/bokeh_static.py` (with cdn and a bit of js)
- [x] `heatmap_demo/static/holoviews_static.py` (huge file and cdn)
- [x] `heatmap_demo/static/plotly_static.py` (huge file no cdn)
- [x] `heatmap_demo/static/d3blocks_static.py` (no slider)

### 2) Dynamic in Python

Another approach is to write all the code in python and have a dynamic webapp that serves the content to the browser. This server can also communicate with the browser and answer requests (such as filtering the dataframe) as the user interacts with the dashboard.

- [x] `heatmap_demo/dynamic/voila_dynamic.py` (uses plotly)
- [x] `heatmap_demo/dynamic/shiny_dynamic.py` (uses plotly)
- [x] `heatmap_demo/dynamic/dash_dynamic.py` (uses plotly)
- [x] `heatmap_demo/dynamic/nicegui_dynamic.py` (uses plotly)
- [x] `heatmap_demo/dynamic/holoviews_dynamic.py` (uses bokeh)
- [x] `heatmap_demo/dynamic/bokeh_dynamic.py` (uses bokeh)
- [ ] `heatmap_demo/dynamic/reflex_dynamic.py` (uses plotly, complicated)
- [ ] `heatmap_demo/dynamic/solara_dynamic.py` (uses plotly, complicated)
- [ ] `heatmap_demo/dynamic/streamlit_dynamic.py` (uses plotly, needs old python)

Summary:

| Framework | How the tech works |
|---------|---------------------------------------------|
| **Voilà** | Jupyter kernel, ipywidgets protocol, notebook-oriented execution |
| **Streamlit** | Script rerun abstraction; widget state drives full re-execution |
| **Shiny** | Reactive dependency graph; fine-grained invalidation of computations |
| **Panel** | High-level layouts, widgets, and app composition on top of Bokeh server |
| **HoloViews** | Declarative plotting; automatic aggregation and gridding of tidy data |
| **Dash** | Explicit callback DAG; React-based frontend; Plotly JSON serialization |
| **NiceGUI** | Python-firsts web UI framework; Vue.js frontend, event-driven callbacks over WebSockets |
| **Bokeh** | Minimal primitives only: data sources, callbacks, and WebSocket patches |
| **Reflex** | Python code wraps real React (Next.js) frontend; state-driven UI |

### 3) Static in Javascript

The third approach is to depart from python, and create a single HTML file that embeds the dataframe as well as the necessary JavaScript to perform all interactive operations on the client side.

- [x] `heatmap_demo/with_js/d3_static.py`
- [x] `heatmap_demo/with_js/echarts.py`
- [x] `heatmap_demo/with_js/observable.py`
- [x] `heatmap_demo/with_js/chartjs.py`
- [x] `heatmap_demo/with_js/nivo_static.py`
- [x] `heatmap_demo/with_js/tui_static.py` (appealing interface)
- [ ] `heatmap_demo/with_js/visx_static.py`

### 4) Dynamic in Javascript

The fourth approach is to start a simple RESTful python app that serves the dataframe as JSON HTTP to any client browser that requests it. All the libraries used above can qualify for this of course. But we have not used this solution as the test dataset is sufficiently small to fit inside the static HTML. A simple server that takes `top_n` as parameter can be found here:

- [x] `heatmap_demo/data/server.py`

### 5) Ship python runtime

The fifth approach is to bundle a python runtime that is sent to client. This is about 40MB, and then we can run any python code directly client side.

See this page that is using Panel running on Pyodide (WebAssembly):

* https://panel.holoviz.org/how_to/interactivity/bind_function.html

Or see "JupyterLite" where notebooks open and run without a backend kernel (also uses Pyodide under the hood)

- [x] `heatmap_demo/with_wasm/`

You just need to serve this directory statically and point your browser to it:

    $ python -m http.server

## Conclusion

The criteria to evaluate how good the heatmap is are the following:
 
- Shows the scale as a nice color gradient with correct units.
- It would be nice to have a logarithmic color scale.
- It would be nice to show the location on the color scale when selecting a cell.
- Shows the x and y axis labels to understand which is importer and which is exporter.
- Ability to display a hover tooltip with the correct label and units.
- Ability to reserve a special separate color for the null values, such as white (while 0.001 would switch to pale yellow).
- The slider should be wide and have clear labeling.
- The labels on the x and y ticks should be rotated when needed for clear display.
- Page should feel responsive when changing the slider.
- The heatmap size should scale with the size of the window.
