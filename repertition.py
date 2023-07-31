import chess
import play
from communication import talk


if __name__ == "__main__":
    play.init()
    try:
        talk(chess.Board(), play.next_move)
    except KeyboardInterrupt:
        pass
    play.cleanup()
