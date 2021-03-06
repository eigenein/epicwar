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


input_option = click.option(
    "input_", "-i", "--input",
    type=click.File("rt"),
    help="Serialized Epic War command log (stdin by default).",
)
output_option = click.option(
    "-o", "--output",
    type=click.File("wt", encoding="utf-8"),
    help="Command log in JSON format (stdout by default).",
)


@main.command()
@input_option
@output_option
def unpack(input_: typing.io.TextIO, output: typing.io.TextIO):
    """
    Unpack serialized command log.
    """
    tokens_iterator = iter_tokens(input_ or click.get_text_stream("stdin", encoding="utf-8"))
    header = read_header(tokens_iterator)
    commands = list(iter_commands(tokens_iterator))

    json.dump(
        {"header": header, "commands": commands},
        output or click.get_text_stream("stdout", encoding="utf-8"),
        indent=2,
    )


def iter_tokens(input_: typing.io.TextIO):
    """
    Iterates over tokens in serialized Epic War command log.
    """
    token = ""
    while True:
        character = input_.read(1)
        if not character:
            break
        if character in ("`", "~", "^", "!"):
            if token:
                yield token
                token = ""
            yield character
        else:
            token += character


def read_header(tokens) -> dict:
    """
    Reads header from the command log.
    """
    expect_token(tokens, "1")
    expect_token(tokens, "^")
    command_id_counter = int(next(tokens))
    expect_token(tokens, "`")
    last_extracted_id = int(next(tokens))
    expect_token(tokens, "`")
    length = int(next(tokens))
    expect_token(tokens, "!")
    return {
        "command_id_counter": command_id_counter,
        "last_extracted_id": last_extracted_id,
        "length": length,
    }


def iter_commands(tokens):
    """
    Iterates over commands in the command log.
    """
    while True:
        token = next(tokens)
        if token == "`":
            # Null command.
            yield None
            continue
        if token == "~":
            # Commands end.
            expect_token(tokens, "0")
            expect_token(tokens, "~")
            break
        # Read command.
        assert token == "1"
        expect_token(tokens, "^")
        col = int(next(tokens))
        expect_token(tokens, "`")
        id_ = int(next(tokens))
        expect_token(tokens, "`")
        kind = next(tokens)
        expect_token(tokens, "`")
        row = int(next(tokens))
        expect_token(tokens, "`")
        time = int(next(tokens))
        expect_token(tokens, "`")
        type_id = int(next(tokens))
        expect_token(tokens, "`")
        expect_token(tokens, "~")
        expect_token(tokens, "1")
        expect_token(tokens, "~")
        yield {"col": col, "id": id_, "kind": kind, "row": row, "time": time, "type_id": type_id}


def expect_token(tokens, token: str):
    """
    Gets the next token and compares it against the provided one.
    """
    if next(tokens) != token:
        raise ValueError("expected: %s" % token)


if __name__ == "__main__":
    main()
