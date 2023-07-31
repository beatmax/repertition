import os
import sys
from pathlib import Path

import chess

import bridge
import chat
from review_book import ReviewBook


books = None


def init():
    global books
    topdir = Path().home() / '.repertition'
    repdir = topdir / 'repertoire'
    revdir = topdir / 'review'
    engine_path = topdir / 'engine'

    os.makedirs(revdir, exist_ok=True)
    os.makedirs(repdir / 'white', exist_ok=True)
    os.makedirs(repdir / 'black', exist_ok=True)
    books = {chess.WHITE: ReviewBook(revdir / 'white.pgn', repdir / 'white', chess.WHITE),
             chess.BLACK: ReviewBook(revdir / 'black.pgn', repdir / 'black', chess.BLACK)}

    if not engine_path.exists() or not os.access(engine_path, os.X_OK):
        sys.exit(f"Missing or not executable: {engine_path}")
    bridge.init(engine_path)


def cleanup():
    bridge.cleanup()


def next_move(board: chess.Board) -> chess.Move:
    if len(board.move_stack) < 2:
        report_review_status()

    user_color = not board.turn
    move, bottom_reached, correct_move = books[user_color].next_move(board)
    if bottom_reached:
        chat.send("You reached the end of this variation, congratulations!")
        report_review_status()
    if correct_move:
        chat.send("Sorry, that's not the move!")
        chat.send(f"Correct move: {correct_move}")
    if not move:
        move = bridge.next_move(board)
    return move


def report_review_status():
    pending_white = books[chess.WHITE].pending_review_count()
    pending_black = books[chess.BLACK].pending_review_count()
    if (pending_white + pending_black) == 0:
        chat.send("No moves left to review, congratulations!")
    else:
        chat.send(f"{pending_white} moves to review as white.")
        chat.send(f"{pending_black} moves to review as black.")
