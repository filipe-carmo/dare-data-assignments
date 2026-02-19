from pathlib import Path
import pandas as pd

# Constants
ID_COLS = ['unit', 'sex', 'age', 'region']


def load_data(file_path: Path) -> pd.DataFrame:
    """
    Load raw EU life expectancy data from TSV file.
    
    Args:
        file_path: Path to the raw TSV file
        
    Returns:
        Raw DataFrame with unparsed first column
    """
    return pd.read_csv(file_path, sep="\t")


def clean_data(raw_df: pd.DataFrame, country: str = "PT") -> pd.DataFrame:
    """
    Clean and transform life expectancy data.

    Transforms wide format to long format, extracts metadata,
    and filters for country records with valid values.

    Args:
        raw_df: Raw DataFrame from TSV file
        country: Country code to filter (default: "PT")

    Returns:
        Cleaned DataFrame for specified country
    """
    df = raw_df.copy()
    
    # Split first column into metadata fields
    first_col = df.columns[0]
    df[['unit', 'sex', 'age', 'region']] = df[first_col].str.split(',', expand=True)
    df = df.drop(columns=[first_col])

    # Reshape to long format
    id_cols = ID_COLS  # ← Usa constante
    value_cols = [col for col in df.columns if col not in id_cols]

    long_df = df.melt(
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

    # Filter for country with valid values
    clean_df = long_df[
        (long_df['region'] == country) & long_df['value'].notna()
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


def main(country: str = "PT") -> pd.DataFrame:
    """
    Main pipeline: load, clean, and save life expectancy data for a specific country.

    Args:
        country: Country code to filter (default: "PT" for Portugal)
        
    Returns:
        Cleaned DataFrame for testing purposes
        
    Files:
        Input:  data/raw/eu_life_expectancy_raw.tsv
        Output: data/processed/{country}_life_expectancy.csv
    """
    data_path = Path(__file__).resolve().parent / "data"
    raw_path = data_path / "raw" / "eu_life_expectancy_raw.tsv"
    output_path = data_path / "processed" / f"{country.lower()}_life_expectancy.csv"
    
    raw_data = load_data(raw_path)
    cleaned_data = clean_data(raw_data, country=country)
    save_data(cleaned_data, output_path)
    
    return cleaned_data


if __name__ == "__main__":
    main() 