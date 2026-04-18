# Life Expectancy Data Pipeline

[![Python application](https://github.com/filipecarmo/dare-data-assignments/actions/workflows/python-app.yml/badge.svg)](https://github.com/filipecarmo/dare-data-assignments/actions/workflows/python-app.yml)

A robust Python-based data engineering pipeline designed to clean and transform European life expectancy data from Eurostat. This project demonstrates clean code principles, design patterns (Strategy & Factory), comprehensive testing, and automated CI/CD workflows.

## 🚀 Overview

The goal of this project is to process raw life expectancy data which arrives in various formats (TSV, JSON, ZIP) and transform it into a standardized, clean CSV format for downstream analysis. 

### Key Features:
- **Strategy Pattern:** Decouples data loading and cleaning logic for different file formats (TSV and JSON/ZIP).
- **Factory Pattern:** Dynamically selects the appropriate processing strategy based on the input file type.
- **Type Safety:** Utilizes Python type hints and Enums for regions and strategies.
- **Automated Testing:** High test coverage using `pytest` and `pytest-cov`.
- **Code Quality:** Enforced through `pylint` and GitHub Actions CI/CD.

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **Data Processing:** Pandas, Polars
- **Testing:** Pytest, Pytest-cov
- **Linting:** Pylint
- **CI/CD:** GitHub Actions

## 📥 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/filipecarmo/dare-data-assignments.git
   cd dare-data-assignments
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## 📖 Usage

The main entry point for the pipeline is `life_expectancy/cleaning.py`. You can run it directly or import the `main` function.

```bash
python -m life_expectancy.cleaning
```

By default, it processes the Portuguese (PT) data from the default raw data source. You can customize the behavior by modifying the parameters in `main()`.

## 🧪 Testing & Quality Control

To ensure the integrity of the data pipeline, I've implemented a suite of unit and integration tests.

### Run Tests
```bash
pytest --cov=life_expectancy life_expectancy/tests/
```

### Run Linter
```bash
pylint life_expectancy
```

## 📂 Project Structure

```text
.
├── .github/workflows/    # CI/CD configuration
├── course_materials/     # Original assignment instructions and materials
├── life_expectancy/      # Main package
│   ├── data/             # Raw and processed data (ignored by git)
│   ├── tests/            # Unit and integration tests
│   └── cleaning.py       # Core pipeline logic (Strategy/Factory patterns)
├── pyproject.toml        # Project metadata and dependencies
└── README.md             # This file
```

## 📝 Attribution

This project was developed by **Filipe Carmo** as part of the **Foundations Learning Path** (lp-foundations) course. The initial project structure and problem statement were proposed by **DareData Engineering**.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
