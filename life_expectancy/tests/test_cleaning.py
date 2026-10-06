"""Tests for the cleaning module"""

from unittest.mock import patch
from pathlib import Path

import pandas as pd
import pytest

from life_expectancy.cleaning import (
    Region,
    TSVStrategy,
    JSONStrategy,
    DataStrategyFactory,
    save_data,
    main,
    parse_args,
    cli,
)

from . import FIXTURES_DIR


def test_load_data(eu_life_expectancy_raw):
    """Test that load_data correctly reads the TSV into a DataFrame"""
    # 1. Create an instance of the TSV strategy
    strategy = TSVStrategy()

    # 2. Call load_data on the strategy
    actual = strategy.load_data(FIXTURES_DIR / "eu_life_expectancy_raw.tsv")

    pd.testing.assert_frame_equal(actual, eu_life_expectancy_raw)


def test_clean_data(eu_life_expectancy_raw, pt_life_expectancy_expected):
    """Test that clean_data returns the expected output for PT"""
    strategy = TSVStrategy()  # Create the strategy

    # Pass 'raw_df' as the first argument, and 'country' as the second
    pt_life_expectancy_actual = strategy.clean_data(
        eu_life_expectancy_raw, country=Region.PT
    )

    pd.testing.assert_frame_equal(
        pt_life_expectancy_actual, pt_life_expectancy_expected
    )


def test_save_data(pt_life_expectancy_expected):
    """Test that save_data calls to_csv correctly"""
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        save_data(pt_life_expectancy_expected, Path("dummy/path.csv"))
        mock_to_csv.assert_called_once()


def test_main(eu_life_expectancy_raw, pt_life_expectancy_expected):
    """Test main pipeline with mocked strategy and save_data"""

    # 1. We mock the save_data function as usual
    with patch("life_expectancy.cleaning.save_data") as mock_save:

        # 2. We mock the entire Factory's 'get_strategy' method
        with patch(
            "life_expectancy.cleaning.DataStrategyFactory.get_strategy"
        ) as mock_get_strategy:

            # 3. We set up what the "fake" strategy should return
            # We want strategy.load_data to return raw data
            mock_get_strategy.return_value.load_data.return_value = (
                eu_life_expectancy_raw
            )
            # We want strategy.clean_data to return the expected clean data
            mock_get_strategy.return_value.clean_data.return_value = (
                pt_life_expectancy_expected
            )

            # 4. Run main (it will use the mocked factory!)
            result = main(country=Region.PT)

            # 5. Assertions
            mock_save.assert_called_once()
            pd.testing.assert_frame_equal(result, pt_life_expectancy_expected)


def test_actual_countries():
    """Test that actual_countries excludes aggregates and includes real countries"""
    actual = Region.actual_countries()
    assert Region.PT in actual
    assert Region.ES in actual
    assert Region.DE in actual
    assert Region.EU28 not in actual
    assert Region.EFTA not in actual
    assert Region.EA19 not in actual


def test_data_strategy_factory():
    """Test that the factory returns the correct strategy based on file extension"""
    # 1. Test TSV extension
    tsv_strategy = DataStrategyFactory.get_strategy(
        Path("data/raw/eu_life_expectancy_raw.tsv")
    )
    assert isinstance(tsv_strategy, TSVStrategy)

    # 2. Test JSON extension
    json_strategy = DataStrategyFactory.get_strategy(
        Path("data/raw/eurostat_life_expect.zip")
    )
    assert isinstance(json_strategy, JSONStrategy)


def test_json_strategy_clean_data():
    """Test that the JSONStrategy cleans data into the expected standard format"""
    # 1. Create a dummy "raw" JSON DataFrame that mimics the Eurostat structure
    raw_json_data = pd.DataFrame(
        {
            "unit": ["YR", "YR"],
            "sex": ["F", "M"],
            "age": ["Y65", "YLT1"],
            "country": ["PT", "ES"],  # We will filter for PT
            "year": ["2021", "2021"],
            "lifeexpectancy": [21.7, 80.3],
            "flag": ["e", "e"],
            "flagdetail": ["estimated", "estimated"],
        }
    )

    # 2. Create the strategy and call clean_data
    strategy = JSONStrategy()
    cleaned_df = strategy.clean_data(raw_json_data, country=Region.PT)

    # 3. Assertions
    assert len(cleaned_df) == 1
    assert "region" in cleaned_df.columns
    assert "value" in cleaned_df.columns
    assert "country" not in cleaned_df.columns  # Ensure it was renamed
    assert cleaned_df.iloc[0]["region"] == "PT"
    assert cleaned_df.iloc[0]["value"] == 21.7
    assert cleaned_df.iloc[0]["year"] == 2021  # Ensure year is an int


def test_data_strategy_factory_rejects_unknown_format():
    """Unsupported extensions raise a clear error instead of failing later"""
    with pytest.raises(ValueError, match="Unsupported file format"):
        DataStrategyFactory.get_strategy(Path("data/raw/life_expectancy.xlsx"))


def test_tsv_strategy_filters_other_countries(eu_life_expectancy_raw):
    """Cleaning for another region only returns that region's rows"""
    cleaned = TSVStrategy().clean_data(eu_life_expectancy_raw, country=Region.ES)
    assert not cleaned.empty
    assert set(cleaned["region"]) == {"ES"}
    assert cleaned["value"].notna().all()


def test_parse_args_reads_country_and_file():
    """The CLI maps a region code onto the Region enum"""
    args = parse_args(["--country", "ES", "--file", "raw.tsv"])
    assert args.country is Region.ES
    assert args.file == "raw.tsv"


def test_cli_runs_pipeline(pt_life_expectancy_expected, capsys):
    """The CLI forwards its arguments to main and reports the row count"""
    with patch("life_expectancy.cleaning.main", return_value=pt_life_expectancy_expected) as mock_main:
        cli(["--country", "PT", "--file", "raw.tsv"])
    mock_main.assert_called_once_with(country=Region.PT, file_name="raw.tsv")
    assert f"Saved {len(pt_life_expectancy_expected)} rows for PT" in capsys.readouterr().out
