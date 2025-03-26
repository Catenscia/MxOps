# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import re

# -- Retrieve the version from pyproject.toml -------------------------------
this_directory = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(
    os.path.join(this_directory, "../../pyproject.toml"), encoding="utf-8"
) as file:
    content = file.read()

version_pattern = r'\nversion\s*=\s*"(.*)"\n'
pattern_match = re.search(version_pattern, content)
if pattern_match is None:
    raise RuntimeError("Could not retrieve the version from pyproject.toml")
version_string = pattern_match.groups(0)[0]

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MxOps"
copyright = "2025, Catenscia"
author = "Catenscia"
release = version_string
version = version_string

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinx_material", "sphinx_design"]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_material"
html_static_path = ["_static"]

html_theme_options = {
    "nav_title": "MxOps",
    "color_primary": "teal",
    "color_accent": "light-blue",
    "theme_color": "0D7377",
    "repo_url": "https://github.com/Catenscia/MxOps",
    "repo_name": "MxOps",
}


html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

html_logo = "_images/catenscia_logo.png"
