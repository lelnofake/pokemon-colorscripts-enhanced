#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import random
import re
import socket
import sys
from typing import List, Optional

PROGRAM = os.path.realpath(__file__)
PROGRAM_DIR = os.path.dirname(PROGRAM)
COLORSCRIPTS_DIR = f"{PROGRAM_DIR}/colorscripts"

REGULAR_SUBDIR = "regular"
SHINY_SUBDIR = "shiny"

LARGE_SUBDIR = "large"
SMALL_SUBDIR = "small"

SHINY_RATE = 1 / 128
GENERATIONS = {
    "1": (1, 151),
    "2": (152, 251),
    "3": (252, 386),
    "4": (387, 493),
    "5": (494, 649),
    "6": (650, 721),
    "7": (722, 809),
    "8": (810, 905),
    "9": (906, 1025),
    "10": (1026, 1028)
}

_POKEMON_DATA = None


def get_pokemon_data() -> List[dict]:
    global _POKEMON_DATA
    if _POKEMON_DATA is None:
        with open(f"{PROGRAM_DIR}/pokemon.json") as file:
            _POKEMON_DATA = json.load(file)
    return _POKEMON_DATA


def print_file(filepath: str) -> None:
    with open(filepath, "r") as f:
        print(f.read())


def get_candidates_for_gen(generations: str, pokemon_data: List[dict]) -> List[dict]:
    try:
        if "," in generations:
            start_gen = end_gen = random.choice(
                [generation.strip() for generation in generations.split(",")]
            )
        elif "-" in generations:
            start_gen, end_gen = [generation.strip() for generation in generations.split("-", 1)]
        else:
            start_gen = end_gen = generations.strip()

        start_idx = GENERATIONS[start_gen][0]
        end_idx = GENERATIONS[end_gen][1]
        if start_idx > end_idx:
            raise ValueError
    except (KeyError, ValueError):
        print(f"Invalid generation '{generations}'")
        sys.exit(1)

    return pokemon_data[start_idx - 1 : end_idx]


def list_pokemon(
    form_pattern: Optional[str] = None,
    pokemon_name: Optional[str] = None,
    generations: Optional[str] = None,
) -> int:
    pokemon_data = get_pokemon_data()

    # -l -n NAME
    if pokemon_name is not None:
        pk = next((p for p in pokemon_data if p["name"] == pokemon_name), None)
        if not pk:
            print(f"Invalid pokemon '{pokemon_name}'")
            sys.exit(1)
        print(f"{pk['name']}: {', '.join(pk['forms'])}")
        return 1

    # -l -r [GEN]
    if generations is not None:
        candidates = get_candidates_for_gen(generations, pokemon_data)
        # Target pool only includes Pokémon that have alternative forms
        candidates = [p for p in candidates if any(f != "regular" for f in p["forms"])]
        if not candidates:
            print(f"No pokemon with alternate forms found in generation '{generations}'")
            sys.exit(1)
        pk = random.choice(candidates)
        print(f"{pk['name']}: {', '.join(pk['forms'])}")
        return 1

    # -l
    if form_pattern is None:
        for p in pokemon_data:
            print(p["name"])
        return len(pokemon_data)

    compiled_pattern = None
    if form_pattern != "":
        try:
            compiled_pattern = re.compile(form_pattern, re.IGNORECASE)
        except re.error as error:
            print(f"Invalid form regex: {error}")
            sys.exit(1)

    printed = 0
    for p in pokemon_data:
        if form_pattern == "":
            # -l -f: List all pokemon and all of their forms
            print(f"{p['name']}: {', '.join(p['forms'])}")
            printed += 1
        else:
            # -l -f FORM: Regex matching
            if any(compiled_pattern.search(f) for f in p["forms"]):
                print(f"{p['name']}: {', '.join(p['forms'])}")
                printed += 1

    if printed == 0 and form_pattern != "":
        print(f"No pokemon have forms matching regex '{form_pattern}'")
        sys.exit(1)
    return printed


def _draw(name: str, form: str, show_title: bool, shiny: bool, is_small: bool) -> None:
    base_path = COLORSCRIPTS_DIR
    color_subdir = SHINY_SUBDIR if shiny else REGULAR_SUBDIR
    size_subdir = SMALL_SUBDIR if is_small else LARGE_SUBDIR

    # Construct the full name including the form
    display_name = name
    if form and form != "regular":
        display_name += f"-{form}"

    pokemon_file = f"{base_path}/{size_subdir}/{color_subdir}/{display_name}"

    if show_title:
        if shiny:
            print(f"{display_name} (shiny)")
        else:
            print(display_name)
            
    try:
        print_file(pokemon_file)
    except FileNotFoundError:
        print(f"Sprite not found: {pokemon_file}")
        sys.exit(1)


def show_pokemon_by_name(
    name: str, show_title: bool, shiny: bool, is_small: bool, form: Optional[str] = None
) -> None:
    pokemon_data = get_pokemon_data()
    pk = next((p for p in pokemon_data if p["name"] == name), None)
    if not pk:
        print(f"Invalid pokemon '{name}'")
        sys.exit(1)

    if form == "":  # -n NAME -f
        selected_form = random.choice(pk["forms"])
    elif form is not None:  # -n NAME -f FORM
        matched_forms = [f for f in pk["forms"] if f.casefold() == form.casefold()]
        if not matched_forms:
            try:
                compiled = re.compile(form, re.IGNORECASE)
            except re.error as error:
                print(f"Invalid form regex: {error}")
                sys.exit(1)

            matched_forms = [f for f in pk["forms"] if compiled.search(f)]
        if not matched_forms:
            # Fallback on missing form: execute -l -n NAME
            list_pokemon(pokemon_name=name)
            sys.exit(1)
        selected_form = random.choice(matched_forms)
    else:  # -n NAME
        selected_form = "regular"

    _draw(name, selected_form, show_title, shiny, is_small)


def show_random_pokemon(
    generations: str, show_title: bool, shiny: bool, is_small: bool, form: Optional[str], gen_specified: bool
) -> None:
    pokemon_data = get_pokemon_data()
    candidates = get_candidates_for_gen(generations, pokemon_data)

    if form == "":  # -r [GEN] -f
        candidates = [p for p in candidates if any(f != "regular" for f in p["forms"])]
        if not candidates:
            print(f"No pokemon with alternate forms found in generation '{generations}'")
            sys.exit(1)
        pk = random.choice(candidates)
        selected_form = random.choice(pk["forms"])

    elif form is not None:  # -r [GEN] -f FORM
        try:
            compiled = re.compile(form, re.IGNORECASE)
        except re.error as error:
            print(f"Invalid form regex: {error}")
            sys.exit(1)

        valid_pks = [p for p in candidates if any(compiled.search(f) for f in p["forms"])]

        if not valid_pks:
            # Fallback if no match exists
            if gen_specified:
                list_pokemon(generations=generations)
            else:
                list_pokemon(form_pattern=form)
            sys.exit(1)

        pk = random.choice(valid_pks)
        matched_forms = [f for f in pk["forms"] if compiled.search(f)]
        selected_form = random.choice(matched_forms)

    else:  # -r [GEN]
        pk = random.choice(candidates)
        selected_form = "regular"

    if not shiny:
        shiny = random.random() <= SHINY_RATE

    _draw(pk["name"], selected_form, show_title, shiny, is_small)


def show_daily_pokemon(show_title: bool, is_small: bool) -> None:
    today = datetime.date.today()
    # Combine date and hostname for a unique daily seed
    seed_val = f"{today.year}-{today.month}-{today.day}-{socket.gethostname()}"
    
    daily_rng = random.Random(seed_val)
    pokemon_data = get_pokemon_data()
    
    pk = daily_rng.choice(pokemon_data)
    selected_form = daily_rng.choice(pk["forms"])
    
    # Rare deterministic daily shiny
    shiny = daily_rng.random() <= SHINY_RATE
    
    _draw(pk["name"], selected_form, show_title, shiny, is_small)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pokemon-colorscripts",
        description="CLI utility to print out unicode image of a pokemon in your shell",
        usage="pokemon-colorscripts [OPTION] [POKEMON NAME/DEX]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
        epilog="""Examples and combinations:
  -n NAME                 Display NAME in its regular form
  -d DEX                  Display pokemon by pokedex number DEX
  --daily                 Display a daily pokemon unique to your machine
  -n NAME -f              Display a random form of NAME
  -d DEX -f               Display a random form of pokemon DEX
  -n NAME -f FORM         Display FORM of NAME (if unavailable, list its forms)
  -r [GEN]                Display a random pokemon in its regular form
  -r [GEN] -f             Display a random form of a random pokemon
  -r [GEN] -f FORM        Display FORM of a random pokemon that has it
  -l                      List all pokemon names
  -l -f                   List all pokemon and all of their forms
  -l -f REGEX             List pokemon with matching forms and all their forms
  -l -n NAME -f           List all forms of NAME
  -l -d DEX -f            List all forms of pokemon DEX
  -l -r [GEN] -f          List forms of a random pokemon that has alternate forms

GEN may be a generation number, range, or comma-separated list (for example 1,
1-3, or 1,3,6). --name, --dex, --random, and --daily cannot be used together. In list mode,
--form without a value lists forms, and exact form targeting is prohibited
for specific or random pokemon targets. In list mode, FORM is a regular
expression matched against form names, including regular; matching pokemon
are listed with all their forms. --compact and --shiny only affect sprite
display.""",
    )

    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    parser.add_argument(
        "-l", "--list", help="Print list of all pokemon", action="store_true"
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        help="""Select pokemon by name. Generally spelled like in the games.
                a few exceptions are nidoran-f, nidoran-m, mr-mime, farfetchd, flabebe
                type-null etc. Perhaps grep the output of --list if in
                doubt.""",
    )
    parser.add_argument(
        "-d",
        "--dex",
        type=int,
        help="Select pokemon by pokedex number.",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Show a daily pokemon based on the current date and your machine's name.",
    )
    parser.add_argument(
        "-f",
        "--form",
        type=str,
        nargs="?",
        const="",
        default=None,
        metavar="FORM",
        help="Select a form; without a value, choose or list alternate forms",
    )
    parser.add_argument(
        "--no-title", action="store_false", help="Do not display pokemon name"
    )
    parser.add_argument(
        "-s",
        "--shiny",
        action="store_true",
        help="Show the shiny version of the pokemon instead",
    )
    parser.add_argument(
        "-c",
        "--compact",
        action="store_true",
        help="Show a smaller version of the sprite",
    )
    parser.add_argument(
        "-r",
        "--random",
        type=str,
        const="1-10",
        nargs="?",
        default=None,
        metavar="GEN",
        help="""Show a random pokemon. This flag can optionally be
                followed by a generation number or range (1-10) to show random
                pokemon from a specific generation or range of generations.
                The generations can be provided as a continuous range (eg. 1-3)
                or as a list of generations (1,3,6)""",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Enforce mutual exclusivity for targeting modes
    exclusive_flags = sum([
        bool(args.name),
        args.dex is not None,
        args.random is not None,
        args.daily
    ])
    
    if exclusive_flags > 1:
        parser.error("Mutually exclusive flags: -n, -d, -r, and --daily cannot be used together.")

    # Restrict --daily modifiers
    if args.daily:
        if args.list or args.form is not None or args.shiny:
            parser.error("--daily only accepts --no-title and -c/--compact flags.")

    # Translate -d / --dex to -n / --name right after parsing
    if args.dex is not None:
        pokemon_data = get_pokemon_data()
        if args.dex < 1 or args.dex > len(pokemon_data):
            parser.error(f"Invalid dex number '{args.dex}'. Valid range is 1-{len(pokemon_data)}.")
        args.name = pokemon_data[args.dex - 1]["name"]

    gen_specified = args.random is not None

    # Handle Implicit Targets for -f / -f FORM where targets are omitted
    if not args.list and not args.name and args.random is None and not args.daily:
        if args.form is not None:
            args.random = "1-10"
        else:
            parser.print_help()
            sys.exit(0)

    # Isolated Listing Mode Execution (Ignored Drawing variables)
    if args.list:
        if args.name:
            if args.form is not None and args.form != "":
                parser.error("Cannot specify exact form during list operations with a specific pokemon.")
            list_pokemon(pokemon_name=args.name)
        elif args.random is not None:
            if args.form is not None and args.form != "":
                parser.error("Cannot specify exact form during random list operations.")
            list_pokemon(generations=args.random)
        else:
            list_pokemon(form_pattern=args.form)

    # Drawing Mode Executions
    elif args.daily:
        show_daily_pokemon(args.no_title, args.compact)
        
    elif args.name:
        show_pokemon_by_name(args.name, args.no_title, args.shiny, args.compact, args.form)
    
    elif args.random is not None:
        show_random_pokemon(args.random, args.no_title, args.shiny, args.compact, args.form, gen_specified)


if __name__ == "__main__":
    main()