# Medium to Markdown Parser and CLI Tool (Python)

This code is a Python rewrite based on the Rust code "Harshil-Jani/medium-to-markdown".

## Installation

Install directly from pip.

```
pip install medium-to-markdown-py
```

## Usage

The command-line interface (CLI) accepts a Medium blog post URL and a filename as input and generates the Markdown content.

``` python
from medium_to_markdown.Parser import MediumParser

url = "https://~~~~"
filename = ""
output_dir ="medium/origin_md"
is_image_download = True
ssl_verify = True

parser = MediumParser(url, output_dir, filename, is_image_download, ssl_verify)

if parser.parse():
    print("Parsing is done.")

```