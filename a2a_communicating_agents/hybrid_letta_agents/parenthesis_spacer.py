#!/usr/bin/env python3
"""
paren_bracket_spacer.py

Formatting rules (Python source code):

1) Parentheses: add spaces *inside* non-empty parentheses
      foo( x )   ✅
      foo()      ✅ (empty stays unchanged)

2) Brackets: add spaces *inside* non-empty square brackets
      [ x ]      ✅
      []         ✅ (empty stays unchanged)

3) Special list-in-parens tightening (for calls like pytest.main( [ ... ] )):
   If the first non-whitespace character after '(' is '[', remove whitespace
   between '(' and '['.
   If the last non-whitespace character before ')' is ']', remove whitespace
   between ']' and ')'.

   Example:
      pytest.main( [__file__, "-v", "-s"] )
   becomes:
      pytest.main([ __file__, "-v", "-s" ])

Important:
- Parentheses/brackets inside STRING and COMMENT tokens are ignored.
- This tool inserts missing spaces and removes whitespace only for rule (3).
  It does not otherwise normalize existing interior whitespace.

Usage examples:
    # Print formatted file to stdout
    python paren_bracket_spacer.py path/to/file.py

    # Rewrite file in place (creates .bak)
    python paren_bracket_spacer.py path/to/file.py --in-place

    # Format all .py files under a directory
    python paren_bracket_spacer.py path/to/project --recursive --in-place

    # Show a unified diff (does not modify files)
    python paren_bracket_spacer.py path/to/file.py --diff

    # CI-friendly check (prints files needing changes; exit code 1 if any)
    python paren_bracket_spacer.py path/to/project --recursive --check
"""

from __future__ import annotations

import argparse
import difflib
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass( frozen = True )
class Edit:
    start: int
    end: int
    replacement: str


def _compute_line_starts( src: str ) -> List[ int ]:
    starts = [ 0 ]
    for m in re.finditer( r"\n", src ):
        starts.append( m.end() )
    return starts


def _line_col_to_index( line_starts: List[ int ], line: int, col: int ) -> int:
    # tokenize uses 1-based line numbers
    return line_starts[ line - 1 ] + col


def _detect_newline_style( src: str ) -> str:
    # Preserve CRLF if the file is purely CRLF.
    if "\r\n" in src and "\n" in src:
        # If any lone '\n' exists (not preceded by '\r'), treat as mixed and keep '\n'
        if re.search( r"(?<!\r)\n", src ):
            return "\n"
        return "\r\n"
    return "\n"


def _scan_next_non_ws( src: str, i: int ) -> int:
    n = len( src )
    while i < n and src[ i ].isspace():
        i += 1
    return i


def _scan_prev_non_ws( src: str, i: int ) -> int:
    while i >= 0 and src[ i ].isspace():
        i -= 1
    return i


def format_parens_and_brackets( src: str ) -> Tuple[ str, int ]:
    """
    Return ( new_source, num_edits_applied ).
    """
    if not src:
        return src, 0

    line_starts = _compute_line_starts( src )

    # '(' ')' '[' ']' in code are OP tokens.
    # Parentheses/brackets inside strings/comments are not OP tokens, so they're ignored.
    tokens = list( tokenize.generate_tokens( io.StringIO( src ).readline ) )

    edits: List[ Edit ] = []
    n = len( src )

    for tok_type, tok_str, start, end, _ in tokens:
        if tok_type != tokenize.OP or tok_str not in ( "(", ")", "[", "]" ):
            continue

        start_idx = _line_col_to_index( line_starts, start[ 0 ], start[ 1 ] )
        end_idx = _line_col_to_index( line_starts, end[ 0 ], end[ 1 ] )

        if tok_str == "(":
            # Empty parens?
            j = _scan_next_non_ws( src, end_idx )
            if j < n and src[ j ] == ")":
                continue

            # Special tightening: "(   [" -> "(["
            if j < n and src[ j ] == "[":
                if j != end_idx:
                    edits.append( Edit( start = end_idx, end = j, replacement = "" ) )
                continue

            # Otherwise: ensure at least one space after '(' if immediately followed by non-space
            if end_idx < n and not src[ end_idx ].isspace():
                edits.append( Edit( start = end_idx, end = end_idx, replacement = " " ) )

        elif tok_str == ")":
            # Empty parens?
            j = _scan_prev_non_ws( src, start_idx - 1 )
            if j >= 0 and src[ j ] == "(":
                continue

            # Special tightening: "]   )" -> "])"
            if j >= 0 and src[ j ] == "]":
                ws_start = j + 1
                ws_end = start_idx
                if ws_end > ws_start:
                    edits.append( Edit( start = ws_start, end = ws_end, replacement = "" ) )
                continue

            # Otherwise: ensure at least one space before ')' if immediately preceded by non-space
            if start_idx - 1 >= 0 and not src[ start_idx - 1 ].isspace():
                edits.append( Edit( start = start_idx, end = start_idx, replacement = " " ) )

        elif tok_str == "[":
            # Empty brackets?
            j = _scan_next_non_ws( src, end_idx )
            if j < n and src[ j ] == "]":
                continue

            # Ensure at least one space after '[' if immediately followed by non-space
            if end_idx < n and not src[ end_idx ].isspace():
                edits.append( Edit( start = end_idx, end = end_idx, replacement = " " ) )

        else:  # tok_str == "]"
            # Empty brackets?
            j = _scan_prev_non_ws( src, start_idx - 1 )
            if j >= 0 and src[ j ] == "[":
                continue

            # Ensure at least one space before ']' if immediately preceded by non-space
            if start_idx - 1 >= 0 and not src[ start_idx - 1 ].isspace():
                edits.append( Edit( start = start_idx, end = start_idx, replacement = " " ) )

    if not edits:
        return src, 0

    # Apply edits right-to-left to keep indexes stable.
    edits_sorted = sorted( edits, key = lambda e: ( e.start, e.end ), reverse = True )
    out = src
    for e in edits_sorted:
        out = out[ : e.start ] + e.replacement + out[ e.end : ]

    return out, len( edits )


def iter_py_files( paths: Iterable[ Path ], recursive: bool ) -> Iterable[ Path ]:
    for p in paths:
        if p.is_dir():
            if recursive:
                yield from p.rglob( "*.py" )
            else:
                continue
        else:
            yield p


def format_file(
    path: Path,
    in_place: bool,
    make_backup: bool,
    show_diff: bool,
    print_output: bool,
) -> Tuple[ bool, int ]:
    """
    Returns ( changed, edits_applied ).
    """
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding( io.BytesIO( data ).readline )
    src = data.decode( encoding, errors = "surrogateescape" )

    newline_style = _detect_newline_style( src )

    formatted, edits_applied = format_parens_and_brackets( src )
    if newline_style == "\r\n":
        formatted = formatted.replace( "\n", "\r\n" )

    changed = ( formatted != src )

    if show_diff and changed:
        diff = difflib.unified_diff(
            src.splitlines( keepends = True ),
            formatted.splitlines( keepends = True ),
            fromfile = str( path ),
            tofile = f"{path} (formatted)",
        )
        sys.stdout.writelines( diff )

    if in_place and changed:
        if make_backup:
            backup_path = path.with_suffix( path.suffix + ".bak" )
            backup_path.write_bytes( data )

        path.write_bytes( formatted.encode( encoding, errors = "surrogateescape" ) )

    if print_output and not in_place and not show_diff:
        sys.stdout.write( formatted )

    return changed, edits_applied


def build_arg_parser( ) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description = "Insert spaces inside non-empty parentheses and brackets in Python code.",
    )
    p.add_argument( "paths", nargs = "+", help = "File(s) and/or directory(ies) to process" )
    p.add_argument( "--recursive", action = "store_true", help = "Recurse into directories" )
    p.add_argument( "--in-place", action = "store_true", help = "Rewrite files in place" )
    p.add_argument( "--no-backup", action = "store_true", help = "Do not create .bak backups (only with --in-place)" )
    p.add_argument( "--check", action = "store_true", help = "Exit 1 if changes are needed; do not write files" )
    p.add_argument( "--diff", action = "store_true", help = "Show unified diff; do not write files" )
    return p


def main( argv: List[ str ] ) -> int:
    args = build_arg_parser().parse_args( argv )

    raw_paths = [ Path( p ) for p in args.paths ]
    files = list( iter_py_files( raw_paths, recursive = args.recursive ) )

    if not files:
        return 0

    any_changed = False
    total_edits = 0

    print_output = ( not args.in_place and not args.check and not args.diff and len( files ) == 1 )

    for f in files:
        if not f.exists() or not f.is_file():
            continue

        changed, edits_applied = format_file(
            f,
            in_place = args.in_place and not args.check and not args.diff,
            make_backup = ( not args.no_backup ),
            show_diff = args.diff,
            print_output = print_output,
        )
        if changed:
            any_changed = True
            total_edits += edits_applied
            if args.check:
                print( str( f ) )

    if args.check:
        return 1 if any_changed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit( main( sys.argv[ 1 : ] ) )
