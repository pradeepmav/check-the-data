# check-the-data

Quick descriptive statistics for [Polars](https://pola.rs/) DataFrames — exported to Excel in one call.

Built for Machine Learning / Data Science workflows where you need a rapid, comprehensive statistical profile of every column: data type, missing values, distinct values, min/max, mean, median, mode, and missing percentage.

## Features

- Works with large files (> 200 GB) via Polars
- One-shot Excel output with polished table formatting
- Automatic fallback to Pandas / CSV if Excel write fails
- Handles numeric and non-numeric columns safely

## Installation

```bash
pip install check-the-data
```

Or install from source:

```bash
git clone https://github.com/pradeepmav/check_the_data.git
cd check_the_data
pip install -e .
```

## Usage

```python
import polars as pl
import check_the_data

# Load your data
df = pl.read_csv("your_data.csv")

# Generate descriptive statistics
result = check_the_data.fact_check_of_the_data(
    dataframe=df,
    output_dir="./reports",
    workbook_name="data_profile"
)
print(result)
```

## Requirements

- Python >= 3.9
- polars >= 0.20.0
- pandas >= 1.5.0 (fallback)
- xlsxwriter >= 3.0.0

## License

MIT
