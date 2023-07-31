import sys
from typing import Any

import chess
from chess.engine import PlayResult

from engine_wrapper import MinimalEngine

sys.path.insert(0, 'repertition')
import chat
import play


class Repertition(MinimalEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        play.init()

    def quit(self):
        play.cleanup()
        super().quit()

    def play_move(self, board, game, li, start_time, move_overhead, can_ponder, is_correspondence, correspondence_move_time, engine_cfg):
        chat.set_send_func(lambda msg: li.chat(game.id, "player", msg))
        super().play_move(board, game, li, start_time, move_overhead, can_ponder, is_correspondence, correspondence_move_time, engine_cfg)

    def search(self, board: chess.Board, *args: Any) -> PlayResult:
        return PlayResult(play.next_move(board), None)
