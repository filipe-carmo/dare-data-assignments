import pandas as pd
from pathlib import Path


def clean_data():
    """
    Clean EU life expectancy data and save PT subset.
    """
    
    # Official path: relative to cleaning.py location
    data_path = Path(__file__).parent / "data"
    raw_path = data_path / "eu_life_expectancy_raw.tsv"

    # 1. Load TSV data
    df = pd.read_csv(raw_path, sep="\t")

    # 2. Split first compound column (unit,sex,age,region)
    first_col = df.columns[0]
    df[['unit', 'sex', 'age', 'region']] = df[first_col].str.split(',', expand=True)
    df = df.drop(columns=[first_col])
    
    return df


if __name__ == "__main__":
    df = clean_data()
