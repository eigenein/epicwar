#!/usr/bin/env python3
# coding: utf-8

"""
Used to generate game library module.
"""

import gzip
import json
import typing

import click
import requests


@click.command()
@click.option("-o", "--output", type=click.File("wt", encoding="utf-8"))
@click.argument("url")
def main(url: str, output: typing.io.TextIO):
    """
    Generate game library module.
    """
    content = json.loads(gzip.decompress(requests.get(url).content).decode("utf-8"))
    output = output or click.get_text_stream("stdout")

    print("\n".join((
        "#!/usr/bin/env python3",
        "# coding: utf-8",
        "",
        "\"\"\"",
        "DO NOT EDIT. AUTOMATICALLY GENERATED FROM %s." % url,
        "CONTAINS EPIC WAR STATIC LIBRARY CONTENT.",
        "\"\"\"",
        "",
        "import json",
        "",
        "",
        "CONTENT = json.loads(r\"\"\"",
        json.dumps(content, indent=2, sort_keys=True, ensure_ascii=False),
        "\"\"\")",
    )), file=output)


if __name__ == "__main__":
    main()
