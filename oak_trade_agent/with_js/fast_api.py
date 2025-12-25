#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.responses import JSONResponse

###############################################################################
app = FastAPI()

df = ...  # pandas DataFrame

@app.get("/data")
def data():
    # Send the raw rows you need (or pre-aggregate if huge)
    out = df[["exporter_name", "importer_name", "quantity"]].to_dict(orient="records")
    return JSONResponse(out)