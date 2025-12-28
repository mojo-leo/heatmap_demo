#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The main object of our package
from heatmap_demo.static.vega_static import vega_heatmap


# The main function to run when we are called #
def main():
    return vega_heatmap()


# Execute when run, not when imported
if __name__ == "__main__":
    main()
