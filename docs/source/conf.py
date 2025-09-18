import os
import sys

# -- Path setup --------------------------------------------------------------
# Add project root and src/templify to sys.path so autodoc can import code
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
project = 'Templify-SDK'
copyright = '2025, Devpro LLC'
author = 'Devpro LLC'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",       # Pull in docstrings from code
    "sphinx.ext.napoleon",      # Support Google/NumPy style docstrings
    "sphinx_autodoc_typehints", # Show type hints in docs
    "sphinx.ext.viewcode",      # Link to highlighted source
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'   # Cleaner theme than alabaster
html_static_path = ['_static']

# Optional: set autodoc defaults (so you don’t have to repeat everywhere)
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
