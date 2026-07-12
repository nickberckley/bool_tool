# Configuration file for the Sphinx documentation builder.

project = 'Bool Tool'
copyright = '2026, Nika Kutsniashvili (nickberckley)'
author = 'Nika Kutsniashvili (nickberckley)'
release = '2.0'

extensions = [
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ['templates']
exclude_patterns = []

html_theme = 'furo'
# html_static_path = ["static"]

html_extra_path = [
    "../pages/.images"
]

# `myst_parser` settings.
myst_heading_anchors = 3
myst_enable_extensions = [
    "colon_fence",
]
