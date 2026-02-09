from pathlib import Path
import pandas as pd

def clean_data():
    """
    Clean EU life expectancy data and save PT subset.
    """
    data_path = Path(__file__).parent / "data"
    raw_path = data_path / "eu_life_expectancy_raw.tsv"

    raw_df = pd.read_csv(raw_path, sep="\t")

    first_col = raw_df.columns[0]
    raw_df[['unit', 'sex', 'age', 'region']] = raw_df[first_col].str.split(',', expand=True)
    raw_df = raw_df.drop(columns=[first_col])

    id_cols = ['unit', 'sex', 'age', 'region']
    value_cols = [col for col in raw_df.columns if col not in id_cols]

    long_df = raw_df.melt(id_vars=id_cols, value_vars=value_cols, var_name='year', value_name='value')

    long_df['year'] = long_df['year'].str.extract('(\\d+)').astype(int)
    long_df['value'] = (long_df['value']
                       .astype(str)
                       .str.replace(r'[^\d.]', '', regex=True)
                       .replace('', float('nan'))
                       .astype(float))

    clean_df = long_df[(long_df['region'] == 'PT') & long_df['value'].notna()].reset_index(drop=True)

    output_path = Path("life_expectancy") / "data" / "pt_life_expectancy.csv"
    clean_df.to_csv(output_path, index=False)

    return clean_df
