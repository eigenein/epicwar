#!/usr/bin/env python3
# coding: utf-8

"""
Unpack serialized battle data. Works both as a module and a tool.
"""

import collections
import typing

import click


Attacker = collections.namedtuple("Attacker", "")
BattleConfig = collections.namedtuple("BattleConfig", "")
Defender = collections.namedtuple("Defender", "")


def unpack_config(input_: typing.io.TextIO):
    """
    Unpacks battle config.
    """
    pass


def iter_tokens(input_: typing.io.TextIO):
    """
    Iterates over tokens in serialized Epic War data.
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


@click.group()
def main():
    """
    Unpack serialized battle data.
    """
    pass


@click.option("input_", "-i", "--input", help="Serialized battle config.", type=click.File("rt"))
@click.option("-o", "--output", help="Battle config JSON.")
def config(input_: typing.io.TextIO, output: typing.io.TextIO):
    """
    Unpack serialized battle config.
    """
    input_ = input_ or click.get_text_stream("stdin")
    output = output or click.get_text_stream("stdout")


if __name__ == "__main__":
    main()
