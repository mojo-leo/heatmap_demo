
# Development Workflow

- Write commit hash to AGENTS.md when committing code
- Follow NumPy docstrings, type hints, line length 88.
- Comments should explain scientific rationale. Include references to relevant
  literature and standards where applicable
- Use pandas for data manipulation, ensure reproducible code.
- Use black for code formatting

# Backend

Language: in python
Based on trade data from BACI

Sample data is based on Oak roundwood and sawnwood 440791.


# Front end

In single html file with css and javascript


# Operations Performed

- 46022ba Renamed DataFrame columns in `scripts/load_baci_data.py` function
  `load_from_baci_dump` from original BACI codes (t, i, j, k, v, q) to descriptive
  names: year, exporter, importer, product, value, quantity.

- Modified `load_from_baci_dump` function to accept `product_code` parameter and filter the DataFrame by product code.
- Updated `if __name__ == "__main__"` section to pass 440791 as the product_code.


