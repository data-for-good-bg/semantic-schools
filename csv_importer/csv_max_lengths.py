#!/usr/bin/env python3

import pandas as pd
import sys

def calc_max_lengths(csv_file: str) -> None:
    data = pd.read_csv(csv_file)

    # Calculate max lengths for each column
    for column in data.columns:
        max_len = data[column].astype(str).str.len().max()
        print(f"Column '{column}' max length: {max_len}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python calc_lengths.py <csv_file>")
        sys.exit(1)

    calc_max_lengths(sys.argv[1])
