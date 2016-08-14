#!/usr/bin/env python3
# coding: utf-8

"""
Manipulate battle command log.
Reverse-engineered from CommandLog.as.
"""

import json
import typing

import click


@click.group()
def main():
    """
    Manipulate battle command log.
    """
    pass


@main.command()
@click.option("input_", "-i", "--input", help="Serialized command log.", required=True)
@click.option("-o", "--output", type=click.File("wt"))
def unpack(input_: str, output: typing.io.TextIO):
    """
    Unpack serialized command log.
    """
    assert input_.startswith("1^")
    input_ = input_[2:]

    command_id_counter, input_ = input_.split("`", maxsplit=1)
    last_extracted_id, input_ = input_.split("`", maxsplit=1)
    length, input_ = input_.split("!", maxsplit=1)

    json.dump({
        "command_id_counter": int(command_id_counter),
        "last_extracted_id": int(last_extracted_id),
        "length": int(length),
    }, output or click.get_text_stream("stdout", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
