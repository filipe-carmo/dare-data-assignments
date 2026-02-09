from pathlib import Path
import pandas as pd


def load_data(file_path: Path) -> pd.DataFrame:
    """
    Load raw EU life expectancy data from TSV file.
    
    Args:
        file_path: Path to the raw TSV file
        
    Returns:
        Raw DataFrame with unparsed first column
    """
    return pd.read_csv(file_path, sep="\t")


def clean_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform life expectancy data.
    
    Transforms wide format to long format, extracts metadata,
    and filters for Portugal records with valid values.
    
    Args:
        raw_df: Raw DataFrame from TSV file
        
    Returns:
        Cleaned DataFrame with PT data only
    """
    # Split first column into metadata fields
    first_col = raw_df.columns[0]
    raw_df[['unit', 'sex', 'age', 'region']] = raw_df[first_col].str.split(',', expand=True)
    raw_df = raw_df.drop(columns=[first_col])

    # Reshape to long format
    id_cols = ['unit', 'sex', 'age', 'region']
    value_cols = [col for col in raw_df.columns if col not in id_cols]

    long_df = raw_df.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name='year',
        value_name='value'
    )

    # Parse year and value columns
    long_df['year'] = long_df['year'].str.extract(r'(\d+)').astype(int)
    long_df['value'] = (
        long_df['value']
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', float('nan'))
        .astype(float)
    )

    # Filter for Portugal with valid values
    clean_df = long_df[
        (long_df['region'] == 'PT') & long_df['value'].notna()
    ].reset_index(drop=True)

    return clean_df


def save_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save cleaned data to CSV file.
    
    Args:
        df: Cleaned DataFrame to save
        output_path: Path where CSV will be saved
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def main() -> pd.DataFrame:
    """
    Main pipeline: load, clean, and save life expectancy data.
    
    Returns:
        Cleaned DataFrame for testing purposes
    """
    # Define paths
    data_path = Path(__file__).resolve().parent / "data"
    raw_path = data_path / "eu_life_expectancy_raw.tsv"
    output_path = data_path / "pt_life_expectancy.csv"

    # Execute pipeline
    raw_data = load_data(raw_path)
    cleaned_data = clean_data(raw_data)
    save_data(cleaned_data, output_path)

    return cleaned_data


if __name__ == "__main__":
    main()
