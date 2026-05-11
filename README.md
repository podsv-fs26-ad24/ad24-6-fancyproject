
# Environment and Project Setup
## Python Environment Setup and Management with uv
Make sure to have uv installed: https://docs.astral.sh/uv/getting-started/installation/

After cloning the repository,  create the python environment with all dependencies based on the `.python-version`, `pyproject.toml` and `uv.lock` files by running
```bash
uv sync
```

To add new dependencies, use
```bash
uv add <package>
```
which will add the package to `pyproject.toml` and update the `uv.lock` file. You can also specify a version, e.g. `uv add pandas==2.0.3`.

Remove packages with
```bash
uv remove <package>
```

Commit changes to `pyproject.toml` and `uv.lock` files into version control.

Run `uv sync` after pulling changes to update the local environment.


## Project Directory Organization
The 
```
.
|+-.github/
|
|+-data/
|   |   ->  data in csv-Format for import by cleanup script
|   |+-clean/   -> cleaned data in parquet-format for import by dashboard
|
|+-data_acquisition/    -> raw data with links to sources and documentation
|
|+-deployment/
|
|+-docs/    -> quarto files for the project documentation
|
|+-eda/     -> script to generate eda reports & eda reports
|
|+-src/     -> scripts to run data-cleanup and Dashboard
|
|.env.template
|.gitignore
|.python-version
|README.md
```

# Run Project 
## Run Data cleaning Script

In Windows:
```powershell
py ./src/import_and_cleaning.py
```

## Start Streamlit Dashboard locally
In Windows:
```powershell
streamlit run ./src/Conflict_Overview.py
```

The Dashboard will then be available here: [Dashboard](http://localhost:8501/)


# Project Documentation
The Project Documentation is published [here](https://podsv-fs26-ad24.github.io/ad24-6-fancyproject/).


