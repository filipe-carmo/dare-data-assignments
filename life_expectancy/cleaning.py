"""Clean Eurostat life expectancy data into a tidy, per-country CSV.

The pipeline picks a loading/cleaning strategy from the input file type
(Strategy + Factory patterns), so new formats only need a new strategy class.
"""

import argparse
from enum import Enum
from pathlib import Path
from typing import Protocol

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_RAW_FILE = "eurostat_life_expect.zip"


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
            country: Region to filter (default: Region.PT)

        Returns:
            Cleaned DataFrame for specified country
        """
        df = raw_df.copy()

        # Split first column into metadata fields
        first_col = df.columns[0]
        df[ID_COLS] = df[first_col].str.split(",", expand=True)
        df = df.drop(columns=[first_col])

        # Reshape to long format
        value_cols = [col for col in df.columns if col not in ID_COLS]

        long_df = df.melt(
            id_vars=ID_COLS, value_vars=value_cols, var_name="year", value_name="value"
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
        return pd.read_json(file_path, compression="zip")

    def clean_data(
        self, raw_df: pd.DataFrame, country: Region = Region.PT
    ) -> pd.DataFrame:
        """Cleans the JSON dataframe to match the expected standard format."""
        df = raw_df.copy()

        # Align column names with the TSV output schema
        df = df.rename(columns={"country": "region", "lifeexpectancy": "value"})

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        mask = (df["region"] == country.value) & df["value"].notna()
        clean_df = df.loc[mask, ID_COLS + ["year", "value"]].copy()

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
        if path_str.endswith((".json", ".zip")):
            return JSONStrategy()
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
    country: Region = Region.PT, file_name: str = DEFAULT_RAW_FILE
) -> pd.DataFrame:
    """
    Run the pipeline: load, clean and save life expectancy data for one country.

    Args:
        country: Region to keep in the output
        file_name: Raw file inside ``life_expectancy/data/raw`` (.tsv, .json or .zip)

    Returns:
        The cleaned DataFrame (also written to ``data/processed``)
    """
    raw_path = DATA_DIR / "raw" / file_name
    output_path = DATA_DIR / "processed" / f"{country.value.lower()}_life_expectancy.csv"

    strategy = DataStrategyFactory.get_strategy(raw_path)
    raw_data = strategy.load_data(raw_path)
    cleaned_data = strategy.clean_data(raw_data, country=country)
    save_data(cleaned_data, output_path)

    return cleaned_data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--country",
        type=Region,
        default=Region.PT,
        choices=list(Region),
        metavar="CODE",
        help="Eurostat region code to keep, e.g. PT, ES, DE (default: PT)",
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_RAW_FILE,
        help=f"raw file name inside life_expectancy/data/raw (default: {DEFAULT_RAW_FILE})",
    )
    return parser.parse_args(argv)


def cli(argv: list[str] | None = None) -> None:
    """Command-line entry point (installed as ``life-expectancy``)."""
    args = parse_args(argv)
    cleaned = main(country=args.country, file_name=args.file)
    print(f"Saved {len(cleaned)} rows for {args.country.value}")


if __name__ == "__main__":  # pragma: no cover
    cli()
