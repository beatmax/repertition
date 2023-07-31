# Taken from Andoma (https://github.com/healeycodes/andoma), with minimum changes.
# MIT License, Copyright (c) 2020 Andrew Healey

import chess
import argparse


def talk(board: chess.Board, next_move):
    """
    The main input/output loop.
    This implements a slice of the UCI protocol.
    """
    end = None
    while end is None:
        msg = input()
        end = command(board, next_move, msg)


def command(board: chess.Board, next_move, msg: str):
    """
    Accept UCI commands and respond.
    The board state is also updated.
    """
    msg = msg.strip()
    tokens = msg.split(" ")
    while "" in tokens:
        tokens.remove("")

    if msg == "quit":
        return True

    if msg == "uci":
        print("id name RepeRtition")
        print("id author Maximiliano Pin")
        print("uciok")
        return

    if msg == "isready":
        print("readyok")
        return

    if msg == "ucinewgame":
        return

    if msg.startswith("position"):
        if len(tokens) < 2:
            return

        # Set starting position
        if tokens[1] == "startpos":
            board.reset()
            moves_start = 2
        elif tokens[1] == "fen":
            fen = " ".join(tokens[2:8])
            board.set_fen(fen)
            moves_start = 8
        else:
            return

        # Apply moves
        if len(tokens) <= moves_start or tokens[moves_start] != "moves":
            return

        for move in tokens[(moves_start+1):]:
            board.push_uci(move)

    if msg == "d":
        # Non-standard command, but supported by Stockfish and helps debugging
        print(board)
        print(board.fen())

    if msg[0:2] == "go":
        _move = next_move(board)
        print(f"bestmove {_move}")
        return
