from enum import Enum
from pathlib import Path
from typing import Protocol
import pandas as pd


class Region(Enum):
    AL = "AL"
    AM = "AM"
    AT = "AT"
    AZ = "AZ"
    BE = "BE"
    BG = "BG"
    BY = "BY"
    CH = "CH"
    CY = "CY"
    CZ = "CZ"
    DE = "DE"
    DE_TOT = "DE_TOT"
    DK = "DK"
    EA18 = "EA18"
    EA19 = "EA19"
    EE = "EE"
    EEA30_2007 = "EEA30_2007"
    EEA31 = "EEA31"
    EFTA = "EFTA"
    EL = "EL"
    ES = "ES"
    EU27_2007 = "EU27_2007"
    EU27_2020 = "EU27_2020"
    EU28 = "EU28"
    FI = "FI"
    FR = "FR"
    FX = "FX"
    GE = "GE"
    HR = "HR"
    HU = "HU"
    IE = "IE"
    IS = "IS"
    IT = "IT"
    LI = "LI"
    LT = "LT"
    LU = "LU"
    LV = "LV"
    MD = "MD"
    ME = "ME"
    MK = "MK"
    MT = "MT"
    NL = "NL"
    NO = "NO"
    PL = "PL"
    PT = "PT"
    RO = "RO"
    RS = "RS"
    RU = "RU"
    SE = "SE"
    SI = "SI"
    SK = "SK"
    SM = "SM"
    TR = "TR"
    UA = "UA"
    UK = "UK"
    XK = "XK"

    @classmethod
    def actual_countries(cls) -> list["Region"]:
        """Returns only actual countries, excluding aggregates and groups."""
        non_countries = {
            cls.DE_TOT,
            cls.EA18,
            cls.EA19,
            cls.EEA30_2007,
            cls.EEA31,
            cls.EFTA,
            cls.EU27_2007,
            cls.EU27_2020,
            cls.EU28,
        }
        return [region for region in cls if region not in non_countries]


# Constants
ID_COLS = ["unit", "sex", "age", "region"]


class FileStrategy(Protocol):
    def load_data(self, file_path: Path) -> pd.DataFrame:
        """Loads data from a file."""

    def clean_data(self, raw_df: pd.DataFrame, country: Region) -> pd.DataFrame:
        """Cleans the loaded dataframe."""


class TSVStrategy:

    def load_data(self, file_path: Path) -> pd.DataFrame:
        """
        Load raw EU life expectancy data from TSV file.

        Args:
            file_path: Path to the raw TSV file

        Returns:
            Raw DataFrame with unparsed first column
        """
        return pd.read_csv(file_path, sep="\t")

    def clean_data(
        self, raw_df: pd.DataFrame, country: Region = Region.PT
    ) -> pd.DataFrame:
        """
        Clean and transform life expectancy data.

        Transforms wide format to long format, extracts metadata,
        and filters for country records with valid values.

        Args:
            raw_df: Raw DataFrame from TSV file
            country: Region to filter (default: "PT")

        Returns:
            Cleaned DataFrame for specified country
        """
        df = raw_df.copy()

        # Split first column into metadata fields
        first_col = df.columns[0]
        df[["unit", "sex", "age", "region"]] = df[first_col].str.split(",", expand=True)
        df = df.drop(columns=[first_col])

        # Reshape to long format
        id_cols = ID_COLS  # ← Usa constante
        value_cols = [col for col in df.columns if col not in id_cols]

        long_df = df.melt(
            id_vars=id_cols, value_vars=value_cols, var_name="year", value_name="value"
        )

        # Parse year and value columns
        long_df["year"] = long_df["year"].str.extract(r"(\d+)").astype(int)
        long_df["value"] = (
            long_df["value"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True)
            .replace("", float("nan"))
            .astype(float)
        )

        # Filter for country with valid values
        clean_df = long_df[
            (long_df["region"] == country.value) & long_df["value"].notna()
        ].reset_index(drop=True)

        return clean_df


class JSONStrategy:
    def load_data(self, file_path: Path) -> pd.DataFrame:
        """Reads a JSON file from a ZIP archive."""
        # Pandas can automatically decompress a zip file if you tell it the compression type!
        return pd.read_json(file_path, compression="zip")

    def clean_data(
        self, raw_df: pd.DataFrame, country: Region = Region.PT
    ) -> pd.DataFrame:
        """Cleans the JSON dataframe to match the expected standard format."""
        df = raw_df.copy()

        # 1. Rename columns to match the standard expected by the tests/TSV
        df = df.rename(columns={"country": "region", "lifeexpectancy": "value"})

        # 2. Filter for the specific country and drop rows where value is missing
        # (Assuming 'value' is already numeric in the JSON, but we can coerce just in case)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        clean_df = df[(df["region"] == country.value) & df["value"].notna()]

        # 3. Ensure we only keep the standard ID_COLS + year + value
        cols_to_keep = ID_COLS + ["year", "value"]
        clean_df = clean_df[cols_to_keep]

        # 4. Ensure year is an integer (and strip out anything else just in case)
        clean_df["year"] = (
            clean_df["year"].astype(str).str.extract(r"(\d+)").astype(int)
        )

        return clean_df.reset_index(drop=True)


class DataStrategyFactory:
    @staticmethod
    def get_strategy(file_path: Path) -> FileStrategy:
        """Returns the appropriate strategy based on file extension."""
        path_str = str(file_path).lower()
        if path_str.endswith(".tsv"):
            return TSVStrategy()

        # Changed elif to if
        if path_str.endswith(".json") or path_str.endswith(".zip"):
            return JSONStrategy()

        # Removed else entirely (if it didn't return above, it hits this raise)
        raise ValueError(f"Unsupported file format: {file_path}")


def save_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save cleaned data to CSV file.

    Args:
        df: Cleaned DataFrame to save
        output_path: Path where CSV will be saved
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def main(
    country: Region = Region.PT, file_name: str = "eurostat_life_expect.zip"
) -> pd.DataFrame:
    """
    Main pipeline: load, clean, and save life expectancy data.
    Now supports multiple file formats.
    """
    data_path = Path(__file__).resolve().parent / "data"
    raw_path = data_path / "raw" / file_name  # Now uses the variable file name
    output_path = (
        data_path / "processed" / f"{country.value.lower()}_life_expectancy.csv"
    )

    # 1. Ask the factory for the right strategy
    strategy = DataStrategyFactory.get_strategy(raw_path)

    # 2. Use the strategy to load and clean
    raw_data = strategy.load_data(raw_path)
    cleaned_data = strategy.clean_data(raw_data, country=country)

    # 3. Save as normal
    save_data(cleaned_data, output_path)

    return cleaned_data


if __name__ == "__main__":
    main()
