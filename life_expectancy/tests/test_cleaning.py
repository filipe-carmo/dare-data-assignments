"""Tests for the cleaning module"""

import pandas as pd
from unittest.mock import patch
from pathlib import Path

from life_expectancy.cleaning import Region, load_data, clean_data, save_data, main

from . import FIXTURES_DIR


def test_load_data(eu_life_expectancy_raw):
    """Test that load_data correctly reads the TSV into a DataFrame"""
    actual = load_data(FIXTURES_DIR / "eu_life_expectancy_raw.tsv")
    pd.testing.assert_frame_equal(actual, eu_life_expectancy_raw)


def test_clean_data(eu_life_expectancy_raw, pt_life_expectancy_expected):
    """Test that clean_data returns the expected output for PT"""
    pt_life_expectancy_actual = clean_data(eu_life_expectancy_raw, country=Region.PT)
    pd.testing.assert_frame_equal(
        pt_life_expectancy_actual, pt_life_expectancy_expected
    )


def test_save_data(pt_life_expectancy_expected):
    """Test that save_data calls to_csv correctly"""
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:
        save_data(pt_life_expectancy_expected, Path("dummy/path.csv"))
        mock_to_csv.assert_called_once()


def test_main(eu_life_expectancy_raw, pt_life_expectancy_expected):
    """Test main pipeline with mocked load_data and save_data"""
    with patch(
        "life_expectancy.cleaning.load_data", return_value=eu_life_expectancy_raw
    ), patch("life_expectancy.cleaning.save_data") as mock_save:
        result = main(country=Region.PT)
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
