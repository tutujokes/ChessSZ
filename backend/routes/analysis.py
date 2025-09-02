from fastapi import APIRouter, Body, HTTPException
from models.game import AnalyzeRequest, AnalyzeResponse, Move, Summary, OpeningInfo
from services.evaluation import evaluate_positions, classify_move, is_missed_win
from utils.fen_openings import classify_move_by_fen, detect_opening_info_by_fen
from config import STOCKFISH_PATH
import chess
import chess.pgn
import io
from utils.stockfish import Engine

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest = Body(...)):
    try:
        if not request.pgn and not request.fen:
            raise HTTPException(status_code=400, detail="Você deve informar um PGN ou FEN para análise.")
        if request.pgn:
            game = chess.pgn.read_game(io.StringIO(request.pgn))
            board = game.board()
            states = []
            ply = 1
            for move in game.mainline_moves():
                san = board.san(move)
                from_sq = chess.square_name(move.from_square)
                to_sq = chess.square_name(move.to_square)
                board.push(move)
                fen = board.fen()
                states.append({
                    "ply": ply,
                    "san": san,
                    "from": from_sq,
                    "to": to_sq,
                    "fen": fen
                })
                ply += 1
        elif request.fen:
            states = [{"ply": 1, "san": "", "from": "", "to": "", "fen": request.fen}]
        else:
            states = []
        fens = [s["fen"] for s in states]
        evals = evaluate_positions(fens, depth=request.depth or 15)
        engine = Engine(STOCKFISH_PATH)
        engine.set_depth(request.depth or 15)
        eco_book = None  # Polyglot removido, abertura será identificada automaticamente
        moves = []
        # Sequência de lances para verificar abertura
        game_moves = []
        all_fens = []  # Coleta todos os FENs para detecção de abertura
        
        for i, s in enumerate(states):
            e = evals[i] if i < len(evals) else {"eval_cp": None, "eval_mate": None}
            fen = s["fen"]
            all_fens.append(fen)  # Coleta o FEN
            played_move = s["san"]
            prev_fen = states[i-1]["fen"] if i > 0 else chess.STARTING_FEN
            best_move_uci = engine.best_move(prev_fen)
            best_cp = best_mate = None
            if best_move_uci:
                engine.make_moves([best_move_uci])
                best_info = engine.eval_fen(prev_fen)
                if best_info["type"] == "cp":
                    best_cp = best_info["value"]
                else:
                    best_mate = best_info["value"]
                board = chess.Board(prev_fen)
                best_move_san = board.san(chess.Move.from_uci(best_move_uci))
            else:
                best_move_san = played_move
            played_cp = e["eval_cp"]
            played_mate = e["eval_mate"]
            missed_win = is_missed_win(best_cp, best_mate, played_cp, played_mate)
            eval_played = played_cp if played_cp is not None else 0
            eval_best = best_cp if best_cp is not None else eval_played
            delta_cp = (eval_best - eval_played) if eval_best is not None and eval_played is not None else 0
            # Adiciona o lance à sequência ANTES de classificar
            game_moves.append(played_move)
            # Passa a sequência completa para verificar se está na linha teórica correta
            move_number = (i + 1) // 2 + 1 if i % 2 == 0 else (i + 1) // 2 + 1  # Número do movimento para as brancas/pretas
            classification = "Chance Perdida" if missed_win else classify_move(delta_cp, played_move, best_move_san, fen, eco_book=eco_book, eval_best=eval_best, eval_played=eval_played, prev_fen=prev_fen, eval_mate=played_mate, full_game_moves=game_moves.copy(), move_number=move_number)
            moves.append(Move(
                **s,
                eval_cp=played_cp,
                eval_mate=played_mate,
                best_move=best_move_san,
                delta_cp=delta_cp,
                classification=classification,
                missed_win=missed_win
            ))
        
        # Detecta a abertura baseada na posição final e anteriores (resolve transposições)
        final_fen = states[-1]["fen"] if states else None
        opening_info = detect_opening_info_by_fen(final_fen, all_fens) if final_fen else None
        
        opening = OpeningInfo(eco=opening_info['eco'], name=opening_info['name']) if opening_info else None
        
        summary = Summary(winner=None, avg_depth=request.depth or 15)
        return AnalyzeResponse(opening=opening, moves=moves, summary=summary)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}. Por favor, verifique os dados enviados ou tente novamente mais tarde.")
