import chess
import chess.engine


TIME_LIMIT = 1

engine = None


def init(command):
    global engine
    engine = chess.engine.SimpleEngine.popen_uci(command)


def cleanup():
    engine.quit()


def next_move(board: chess.Board) -> chess.Move:
    result = engine.play(board, chess.engine.Limit(time=TIME_LIMIT))
    return result.move
