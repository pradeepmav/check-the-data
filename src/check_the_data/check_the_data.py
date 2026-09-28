from pathlib import Path
import polars as pl
import polars.selectors as cs
import pandas as pd


def find_df_name(df: pl.DataFrame) -> str:
    """Find the variable name of a dataframe in the global namespace."""
    return next(
        (name for name, obj in globals().items() if id(obj) == id(df)),
        "unnamed_dataframe",
    )


def fact_check_of_the_data(
    dataframe: pl.DataFrame,
    output_dir: str | None = None,
    workbook_name: str | None = None,
) -> str:
    """Generate comprehensive statistical summaries of a Polars dataframe and export to Excel."""
    try:
        numeric_cols = dataframe.select(cs.numeric()).columns
        summary_rows = []

        # Process each column completely in isolation to guarantee type-safety and avoid pivot errors
        for col_name in dataframe.columns:
            is_numeric = col_name in numeric_cols

            # Safely resolve mode (handles ties gracefully by extracting the first element)
            mode_series = dataframe.select(pl.col(col_name).drop_nulls().mode()).to_series()
            mode_val = str(mode_series[0]) if not mode_series.is_empty() else None

            stats = dataframe.select([
                pl.col(col_name).null_count().alias("missing"),
                pl.col(col_name).count().alias("non_missing"),
                pl.col(col_name).n_unique().alias("distinct"),
                pl.col(col_name).min().cast(pl.Utf8).alias("min"),
                pl.col(col_name).max().cast(pl.Utf8).alias("max"),
                pl.col(col_name).mean().alias("mean") if is_numeric else pl.lit(None, dtype=pl.Float64).alias("mean"),
                pl.col(col_name).median().alias("median") if is_numeric else pl.lit(None, dtype=pl.Float64).alias("median"),
            ]).row(0)

            summary_rows.append({
                "Variable_Name": col_name,
                "D_Type": str(dataframe.schema[col_name]),
                "No_of_Non_Missing_Values": stats[1],
                "No_of_Missing_Values": stats[0],
                "Distinct_Values": stats[2],
                "Min": stats[3],
                "Max": stats[4],
                "Mean": round(stats[5], 2) if stats[5] is not None else None,
                "Median": round(stats[6], 2) if stats[6] is not None else None,
                "Mode": mode_val
            })

        # Assemble row structures into final polished Polars DataFrame
        final = pl.DataFrame(summary_rows).with_columns(
            ((pl.col("No_of_Missing_Values") / (pl.col("No_of_Non_Missing_Values") + pl.col("No_of_Missing_Values"))) * 100)
            .round(2)
            .alias("Missing_%")
        )

        # Enforce column sorting, ranking, and arrangement
        final = final.with_columns(S_No=pl.int_range(1, pl.len() + 1)).select(
            "S_No", "Variable_Name", "D_Type", "No_of_Non_Missing_Values", "No_of_Missing_Values",
            "Missing_%", "Distinct_Values", "Min", "Max", "Mean", "Median", "Mode"
        )

        # File System Setup (Pathlib Engine)
        fname = workbook_name or f"{find_df_name(dataframe)}_fact_checks.xlsx"
        out_path = Path(output_dir) / fname if output_dir else Path(fname)
        if output_dir:
            out_path.parent.mkdir(parents=True, exist_ok=True)

        # Writing Protocol Cascade
        try:
            final.write_excel(workbook=str(out_path), worksheet="FCOTD", position="B2", table_style="Table Style Light 10")
            return f"Successfully wrote to Excel: {out_path}"
        except Exception as e:
            print(f"Primary Excel write failed: {e}. Attempting Pandas fallback...")
            try:
                final.to_pandas().to_excel(out_path, sheet_name="FCOTD", index=False, startrow=1, startcol=1)
                return f"Successfully wrote to Excel using pandas fallback: {out_path}"
            except Exception as fallback_error:
                print(f"Fallback Excel write failed: {fallback_error}. Dropping back to CSV...")
                csv_path = out_path.with_suffix(".csv")
                final.write_csv(csv_path)
                return f"Saved as CSV due to total Excel failure: {csv_path}"

    except Exception as e:
        print(f"Error during data analysis: {e}")
        return f"Analysis failed: {str(e)}"
