import pandas as pd
from pathlib import Path


def clean_data():
    """
    Clean EU life expectancy data and save PT subset.
    """
    
    # Official path: relative to cleaning.py
    data_path = Path(__file__).parent / "data"
    raw_path = data_path / "eu_life_expectancy_raw.tsv"

    # 1. Load data
    df = pd.read_csv(raw_path, sep="\t")

    # 2. Split first compound column
    first_col = df.columns[0]
    df[[ 'unit', 'sex', 'age', 'region']] = df[first_col].str.split(',', expand=True)
    df = df.drop(columns=[first_col])

    # 3. Melt to long format (CORRECT ORDER)
    id_cols = ['unit', 'sex', 'age', 'region']
    value_cols = [col for col in df.columns if col not in id_cols]
    
    df_long = df.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name='year',
        value_name='value'
    )

    print("✅ Melted to long format!")
    print(f"Shape: {df_long.shape}")
    print("\n=== SAMPLE ===")
    print(df_long.head(3))
    
    return df_long


if __name__ == "__main__":
    df = clean_data()
