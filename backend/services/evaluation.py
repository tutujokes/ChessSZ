import chess
from utils.openings import classify_opening
from utils.fen_openings import classify_move_by_fen
from utils.stockfish import Engine
from models.game import Move, Summary, AnalyzeResponse

WIN_CP = 300
DRAWISH_CP = 50
INF = 10000

def mover_score_from_eval(eval_cp, eval_mate):
    if eval_mate is not None:
        return -INF if eval_mate > 0 else INF
    if eval_cp is None:
        return 0
    return -eval_cp

def is_missed_win(best_cp, best_mate, played_cp, played_mate):
    best_score   = mover_score_from_eval(best_cp,   best_mate)
    played_score = mover_score_from_eval(played_cp, played_mate)
    if best_score >= INF and played_score < INF:
        return True
    if best_score >= WIN_CP and played_score <= DRAWISH_CP:
        return True
    return False

def is_sacrifice(board, move):
    # Detecta sacrifício simples: entrega peça de maior valor por peça de menor valor
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        moving_piece = board.piece_at(move.from_square)
        if captured_piece and moving_piece:
            values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
            if values[moving_piece.symbol().lower()] > values[captured_piece.symbol().lower()]:
                return True
    return False

def classify_move(delta_cp, played_move, best_move, fen, eco_book=None, eval_best=None, eval_played=None, prev_fen=None, eval_mate=None, full_game_moves=None, move_number=None):
    # Tenta classificar como abertura usando FEN (resolve transposições)
    opening_label = classify_move_by_fen(fen, move_number)
    print(f"DEBUG: classify_move_by_fen retornou: {opening_label} para FEN {fen[:20]}... (movimento {move_number})")
    if opening_label:
        return opening_label
    # Classificação normal
    if eval_mate is not None and eval_mate == 0:
        return "Melhor"
    if eval_mate is not None and eval_mate < 0:
        return "Capivarada"
    delta_abs = abs(delta_cp)
    if delta_abs > 300:
        return "Capivarada"
    board = chess.Board(prev_fen if prev_fen else chess.STARTING_FEN)
    try:
        move_obj = board.parse_san(played_move)
    except Exception:
        move_obj = None
    # Chess.com-style Brilhante: sacrifício correto que mantém avaliação
    if played_move == best_move:
        if move_obj and is_sacrifice(board, move_obj) and abs(eval_best - eval_played) < 50:
            return "Brilhante"
        return "Melhor"
    if delta_abs == 0 and played_move != best_move and eval_best is not None and abs(eval_best) > 300:
        return "Brilhante"
    if 0 < delta_abs <= 20:
        return "Excelente"
    if 20 < delta_abs <= 50:
        return "Bom"
    if 50 < delta_abs <= 100:
        return "Imprecisão"
    if 100 < delta_abs <= 300:
        return "Erro"
    return "Outro"

def evaluate_positions(fens, depth=15, stockfish_path=None):
    engine = Engine(stockfish_path) if stockfish_path else Engine()
    engine.set_depth(depth)
    results = []
    for fen in fens:
        info = engine.eval_fen(fen)
        eval_cp = info.get("value") if info["type"] == "cp" else None
        eval_mate = info.get("value") if info["type"] == "mate" else None
        results.append({"eval_cp": eval_cp, "eval_mate": eval_mate})
    return results
