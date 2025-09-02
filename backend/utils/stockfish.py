from stockfish import Stockfish
from config import STOCKFISH_PATH

class Engine:
    def __init__(self, path=STOCKFISH_PATH):
        self.sf = Stockfish(path)

    def set_depth(self, depth):
        self.sf.set_depth(depth)

    def eval_fen(self, fen, depth=None):
        if depth:
            self.sf.set_depth(depth)
        self.sf.set_fen_position(fen)
        return self.sf.get_evaluation()

    def best_move(self, fen):
        self.sf.set_fen_position(fen)
        return self.sf.get_best_move()

    def make_moves(self, moves):
        self.sf.make_moves_from_current_position(moves)
