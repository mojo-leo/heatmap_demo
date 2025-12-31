#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The main object of our package
from heatmap_demo.static.bokeh_static import bokeh_heatmap


# The main function to run when we are called #
def main():
    return bokeh_heatmap(True)


# Execute when run, not when imported
if __name__ == "__main__":
    main()
