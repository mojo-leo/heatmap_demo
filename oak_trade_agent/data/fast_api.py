#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Third-party modules
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Internal modules
from oak_trade_agent.data.baci_dataset import baci

###############################################################################
# Create the server
app = FastAPI()

# Load the data once at startup
df = baci.ranked_oak_df

@app.get("/data")
def data(top_n: int | None = None):
    """Send the raw rows you need (or pre-aggregate if huge).
    
    Parameters
    ----------
    top_n : int, optional
        If specified, filter to only include entries where both exporter_rank
        and importer_rank are <= top_n. This gives the top N countries and
        all trade relationships between them.
    """
    filtered_df = df
    if top_n is not None:
        filtered_df = df[
            (df["exporter_rank"] <= top_n) & (df["importer_rank"] <= top_n)
        ]
    out = filtered_df[["exporter_name", "importer_name", "quantity"]].to_dict(
        orient="records"
    )
    return JSONResponse(out)

# Run it
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

