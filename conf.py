import os
import sys

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "Prepr API"
copyright = "2023, Connor Rogers, Tristam Sanborn"
author = "Connor Rogers, Tristam Sanborn"
release = "0.68b"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.intersphinx"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The master toctree document.
master_doc = "index"  # default is 'contents', RTD expects 'index'

# -- Options for HTML output -------------------------------------------------

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory.
html_static_path = ["_static"]

# -- Intersphinx configuration ------------------------------------------------

# Example configuration for intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Autodoc configuration ---------------------------------------------------

autodoc_default_options = {
    "member-order": "bysource",
    "special-members": "__init__",
}

# -- Options for Read the Docs -----------------------------------------------

# This is used for linking and such. Useful when building multiple versions
# so that things link to the right version.
version = release

# If using Read the Docs, use the environment variable to determine which
# theme to use.
