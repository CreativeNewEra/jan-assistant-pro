# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Jan Assistant Pro'
copyright = '2025, Your Name'
author = 'Your Name'

import os
import sys
sys.path.insert(0, os.path.abspath("../.."))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinxcontrib.mermaid",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"
mermaid_output_format = "svg"

templates_path = ['_templates']
exclude_patterns = ['_build', 'generated']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
