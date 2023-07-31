import os
import re
import shutil
import sys
import typing

import chess
import chess.pgn

import clk
import review_config

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional


REVIEW_REGEX = re.compile(r"""(?P<prefix>\s?)\[%review\s(?P<isotime>[^]]+)\](?P<suffix>\s?)""")
INTERVAL_REGEX = re.compile(r"""(?P<prefix>\s?)\[%interval\s(?P<days>\d+)\+(?P<hours>\d+):(?P<minutes>\d+)\](?P<suffix>\s?)""")


# copied from python-chess
def _condense_affix(infix: str) -> Callable[[typing.Match[str]], str]:
    def repl(match: typing.Match[str]) -> str:
        if infix:
            return match.group("prefix") + infix + match.group("suffix")
        else:
            return match.group("prefix") and match.group("suffix")
    return repl


class ReviewNode:
    def __init__(self, node):
        self.node = node

    def review_time(self) -> Optional[datetime]:
        match = REVIEW_REGEX.search(self.node.comment)
        if match is None:
            return None
        return datetime.fromisoformat(match.group("isotime"))

    def set_review_time(self, dt: Optional[datetime]) -> None:
        annotation = ""
        if dt is not None:
            annotation = f"[%review {dt.isoformat()}]"

        self.node.comment, found = REVIEW_REGEX.subn(_condense_affix(annotation), self.node.comment, count=1)

        if not found and annotation:
            if self.node.comment and not self.node.comment.endswith(" ") and not self.node.comment.endswith("\n"):
                self.node.comment += " "
            self.node.comment += annotation

    def interval(self) -> Optional[timedelta]:
        match = INTERVAL_REGEX.search(self.node.comment)
        if match is None:
            return None
        return timedelta(days=int(match.group("days")), hours=int(match.group("hours")), minutes=int(match.group("minutes")))

    def set_interval(self, interval: Optional[timedelta]) -> None:
        annotation = ""
        if interval is not None:
            hours = int(interval.seconds // 3600)
            minutes = int(interval.seconds % 3600 // 60)
            annotation = f"[%interval {interval.days:d}+{hours:d}:{minutes:02d}]"

        self.node.comment, found = INTERVAL_REGEX.subn(_condense_affix(annotation), self.node.comment, count=1)

        if not found and annotation:
            if self.node.comment and not self.node.comment.endswith(" ") and not self.node.comment.endswith("\n"):
                self.node.comment += " "
            self.node.comment += annotation


class ReviewBook:
    def __init__(self, path: Path, input_dir: Path, user_color):
        self.path = path
        self.user_color = user_color
        self.tree = chess.pgn.Game()
        self.deleted_moves = 0

        for pgn_path in sorted(input_dir.glob('**/*.pgn')):
            self._merge_pgn(pgn_path)

        if self.path.exists():
            with open(self.path, encoding='utf-8') as pgn:
                review_tree = chess.pgn.read_game(pgn)
            self._update_review_node(review_tree, self.tree)
            self.tree = review_tree
            if self.deleted_moves:
                self._create_backup()

        self._save()

    def next_move(self, board: chess.Board):
        move, bottom_reached, correct_move = None, False, None
        node, previous = self._find_node(board)
        if node:
            if previous and previous is not self.tree:
                self._update(previous, True)
            variation, _, _ = self._find_lowest_review_time(node)
            bottom_reached = not variation or not variation.variations
            if variation:
                move = variation.move
                if bottom_reached:
                    self._update(variation, True)
        elif previous:
            if previous is not self.tree:
                self._update(previous, not previous.variations)
            if previous.variations:
                correct_move = previous.variations[0].san()
        return move, bottom_reached, correct_move

    def pending_review_count(self):
        count = 0
        now = clk.now()
        def visit(review_node):
            nonlocal count, now
            rt = review_node.review_time()
            if not rt or rt <= now:
                count += 1
        self._walk_review_nodes(self.tree, visit)
        return count

    def _walk_review_nodes(self, base, func):
        for v in base.variations:
            if v.turn() == self.user_color:
                func(ReviewNode(v))
            self._walk_review_nodes(v, func)

    def _find_lowest_review_time(self, base):
        variation, node, review_time = None, None, None
        for v in base.variations:
            rt = ReviewNode(v).review_time()
            if not rt:
                rt = clk.now()
            if not review_time or rt < review_time:
                variation, node, review_time = v, v, rt
            if v.variations:
                _, n, rt = self._find_lowest_review_time(v.variations[0])
                if rt and (not review_time or rt < review_time):
                    variation, node, review_time = v, n, rt
        return variation, node, review_time

    def _find_node(self, board: chess.Board):
        previous = None
        try:
            node = self.tree
            for move in board.move_stack:
                previous = node
                node = node.variation(move)
            return node, previous
        except KeyError:
            if previous.ply() != board.ply() - 1:
                previous = None
            return None, previous

    def _update(self, node, correct):
        now = clk.now()
        rn = ReviewNode(node)
        if correct:
            review_time = rn.review_time()
            interval = rn.interval()
        else:
            review_time = None
            interval = None
        if review_time is None:
            review_time = now
        if interval is None:
            interval = review_config.INITIAL_INTERVAL
        if correct:
            was_due = review_time <= now
            review_time = now + interval
            if was_due:
                interval *= review_config.INTERVAL_INC_FACTOR
                if interval > review_config.MAX_INTERVAL:
                    interval = review_config.MAX_INTERVAL
        rn.set_review_time(review_time)
        rn.set_interval(interval)
        self._save()

    def _merge_pgn(self, pgn_path: Path):
        with open(pgn_path, encoding='utf-8') as pgn:
            input_pgn = chess.pgn.read_game(pgn)
        self._merge_node(self.tree, input_pgn)

    def _merge_node(self, dst_node, src_node):
        for src_variation in src_node:
            try:
                dst_variation = dst_node.variation(src_variation.move)
            except KeyError:
                if dst_node.turn() == self.user_color and dst_node.variations:
                    return  # skip alternative user moves (only main move will be accepted)
                dst_variation = dst_node.add_variation(src_variation.move)
            self._merge_node(dst_variation, src_variation)

    def _update_review_node(self, dst_node, src_node):
        for dst_variation in dst_node:
            if not src_node.has_variation(dst_variation.move):
                dst_node.remove_variation(dst_variation.move)
                self.deleted_moves += 1
        for src_variation in src_node:
            try:
                dst_variation = dst_node.variation(src_variation.move)
            except KeyError:
                dst_variation = dst_node.add_variation(src_variation.move)
            self._update_review_node(dst_variation, src_variation)

    def _save(self):
        with open(self.path, 'w', encoding='utf-8') as pgn:
            print(self.tree, file=pgn, end="\n\n")

    def _create_backup(self):
        backup_dir = self.path.parent / 'backup'
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = backup_dir / (self.path.name + '.' + clk.now().isoformat())
        shutil.copyfile(self.path, backup_file)
        print(f"{self.deleted_moves} move(s) deleted, backup created: {backup_file}", file=sys.stderr)
