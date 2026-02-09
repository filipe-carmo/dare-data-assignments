import pandas as pd
import pandas as pd
from pathlib import Path


def clean_data():
    """
    Clean EU life expectancy data and save PT subset.
    """
    
    data_path = Path(__file__).parent / "data"
    raw_path = data_path / "eu_life_expectancy_raw.tsv"

    df = pd.read_csv(raw_path, sep="\t")

    first_col = df.columns[0]
    df[['unit', 'sex', 'age', 'region']] = df[first_col].str.split(',', expand=True)
    df = df.drop(columns=[first_col])

    id_cols = ['unit', 'sex', 'age', 'region']
    value_cols = [col for col in df.columns if col not in id_cols]
    
    df_long = df.melt(id_vars=id_cols, value_vars=value_cols, var_name='year', value_name='value')

    df_long['year'] = df_long['year'].str.extract(r'(\d+)').astype(int)
    df_long['value'] = (df_long['value']
                       .astype(str)
                       .str.replace(r'[^\d.]', '', regex=True)
                       .replace('', float('nan'))
                       .astype(float))
    
    df_clean = df_long[(df_long['region'] == 'PT') & df_long['value'].notna()].reset_index(drop=True)

    # FINAL OUTPUT PATH
    output_path = Path("life_expectancy") / "data" / "pt_life_expectancy.csv"
    df_clean.to_csv(output_path, index=False)
    
    return df_clean


if __name__ == "__main__":
    df = clean_data()
