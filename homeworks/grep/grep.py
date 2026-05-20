import argparse
import re
import sys
from typing import Callable


def output(line: str):
    print(line)


def before_context(
    lines: list[str],
    context: int,
    line_number: int,
    idx: int,
    already_added: set,
    match: Callable[[str], bool],
):
    prefix: str = ""
    left_limit: int = min(idx - 1, context)
    for index, el in enumerate(lines[idx - left_limit - 1 : idx - 1], start=1):
        if el not in already_added:
            if line_number and not match(el):
                prefix = f"{index}-"
            elif line_number and match(el):
                prefix = f"{index}:"
            output(prefix + el)
            already_added.add(el)


def after_context(
    lines: list[str],
    context: int,
    line_number: int,
    idx: int,
    already_added: set,
    match: Callable[[str], bool],
):
    prefix: str = ""
    right_limit: int = min(context, len(lines) - idx)
    for index, el in enumerate(lines[idx : idx + right_limit], start=idx + 1):
        if el not in already_added:
            if line_number and not match(el):
                prefix = f"{index}-"
            elif line_number and match(el):
                prefix = f"{index}:"
            output(prefix + el)
            already_added.add(el)


def grep(lines: list[str], params: argparse.Namespace):
    pattern: str = params.pattern
    if "?" or "*" in pattern:
        if not re.search(r"[^*]", pattern):
            pattern = r"\.*"
        else:
            pattern = pattern.replace("?", ".")

        match: Callable[[str], bool] = lambda line: bool(re.search(pattern, line))

    else:
        match: Callable[[str], bool] = lambda line: params.pattern in line

    if params.ignore_case:
        match: Callable[[str], bool] = lambda line: params.pattern.lower() in line.lower()

    if params.invert:
        match: Callable[[str], bool] = lambda line: params.pattern not in line

    if params.count:
        cnt: int = sum(1 for line in lines if match(line))
        output(str(cnt))

    elif params.context or params.before_context or params.after_context:
        already_added: set = set()
        prefix: str = ""

        for idx, line in enumerate(lines, start=1):
            if match(line):
                if params.context:
                    before_context(
                        lines,
                        params.context,
                        params.line_number,
                        idx,
                        already_added,
                        match,
                    )

                    if line not in already_added:
                        if params.line_number:
                            prefix = f"{idx}:"
                        output(prefix + line)
                        already_added.add(line)

                    after_context(
                        lines,
                        params.context,
                        params.line_number,
                        idx,
                        already_added,
                        match,
                    )

                elif params.before_context:
                    before_context(
                        lines,
                        params.before_context,
                        params.line_number,
                        idx,
                        already_added,
                        match,
                    )

                    if line not in already_added:
                        if params.line_number:
                            prefix: str = f"{idx}:"
                        output(prefix + line)
                        already_added.add(line)

                elif params.after_context:
                    if line not in already_added:
                        if params.line_number:
                            prefix: str = f"{idx}:"
                        output(prefix + line)
                        already_added.add(line)

                    after_context(
                        lines,
                        params.after_context,
                        params.line_number,
                        idx,
                        already_added,
                        match,
                    )

    else:
        for idx, line in enumerate(lines, start=1):
            if params.line_number:
                line: str = f"{idx}:{line}"

            if match(line):
                output(line)


def parse_args(args):
    parser = argparse.ArgumentParser(description="This is a simple grep on python")
    parser.add_argument(
        "-v",
        action="store_true",
        dest="invert",
        default=False,
        help="Selected lines are those not matching pattern.",
    )
    parser.add_argument(
        "-i",
        action="store_true",
        dest="ignore_case",
        default=False,
        help="Perform case insensitive matching.",
    )
    parser.add_argument(
        "-c",
        action="store_true",
        dest="count",
        default=False,
        help="Only a count of selected lines is written to standard output.",
    )
    parser.add_argument(
        "-n",
        action="store_true",
        dest="line_number",
        default=False,
        help="Each output line is preceded by its relative line number in the file, starting at line 1.",
    )
    parser.add_argument(
        "-C",
        action="store",
        dest="context",
        type=int,
        default=0,
        help="Print num lines of leading and trailing context surrounding each match.",
    )
    parser.add_argument(
        "-B",
        action="store",
        dest="before_context",
        type=int,
        default=0,
        help="Print num lines of trailing context after each match",
    )
    parser.add_argument(
        "-A",
        action="store",
        dest="after_context",
        type=int,
        default=0,
        help="Print num lines of leading context before each match.",
    )
    parser.add_argument("pattern", action="store", help="Search pattern. Can contain magic symbols: ?*")
    return parser.parse_args(args)


def main():
    params = parse_args(sys.argv[1:])
    grep(sys.stdin.readlines(), params)


if __name__ == "__main__":
    main()
