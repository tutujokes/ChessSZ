from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import chess.pgn
import io
from stockfish import Stockfish
import traceback

app = FastAPI()

class AnalyzeRequest(BaseModel):
    pgn: Optional[str] = None
    fen: Optional[str] = None
    source: Optional[Literal["pgn", "fen", "lichess", "chess.com"]] = None
    depth: Optional[int] = Field(default=15, ge=1, le=30)

class Move(BaseModel):
    ply: int
    san: str
    from_: str = Field(..., alias="from")
    to: str
    fen: str
    eval_cp: Optional[int] = None
    eval_mate: Optional[int] = None
    best_move: Optional[str] = None
    delta_cp: Optional[int] = None
    classification: str

class Summary(BaseModel):
    winner: Optional[Literal["white", "black", "draw"]] = None
    avg_depth: int

class AnalyzeResponse(BaseModel):
    moves: List[Move]
    summary: Summary

@app.get("/api/health")
def health():
    return {"status": "ok"}

def parse_pgn(pgn_str: str):
    game = chess.pgn.read_game(io.StringIO(pgn_str))
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
    return states

# Função para avaliar uma lista de FENs usando Stockfish
def evaluate_positions(fens, depth=15, stockfish_path="C:/Users/karol/Documents/GitHub/Chessify/backend/stockfish/stockfish-windows-x86-64-avx2.exe"):
    stockfish = Stockfish(stockfish_path)
    stockfish.set_depth(depth)
    results = []
    for fen in fens:
        stockfish.set_fen_position(fen)
        info = stockfish.get_evaluation()
        eval_cp = info.get("value") if info["type"] == "cp" else None
        eval_mate = info.get("value") if info["type"] == "mate" else None
        results.append({"eval_cp": eval_cp, "eval_mate": eval_mate})
    return results

@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest = Body(...)):
    try:
        if not request.pgn and not request.fen:
            raise HTTPException(status_code=400, detail="Você deve informar um PGN ou FEN para análise.")
        # Parse posições
        if request.pgn:
            states = parse_pgn(request.pgn)
        elif request.fen:
            states = [{"ply": 1, "san": "", "from": "", "to": "", "fen": request.fen}]
        else:
            states = []
        fens = [s["fen"] for s in states]
        evals = evaluate_positions(fens, depth=request.depth or 15)
        moves = []
        for i, s in enumerate(states):
            print('DEBUG estado:', s)  # depuração temp
            s_fixed = {**s, "from_": s["from"]}
            e = evals[i] if i < len(evals) else {"eval_cp": None, "eval_mate": None}
            moves.append(Move(
                **s_fixed,
                eval_cp=e["eval_cp"],
                eval_mate=e["eval_mate"],
                best_move=None,
                delta_cp=None,
                classification=""
            ))
        summary = Summary(winner=None, avg_depth=request.depth or 15)
        return AnalyzeResponse(moves=moves, summary=summary)
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()  # Adicionada linha para exibir o erro completo no terminal
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}. Por favor, verifique os dados enviados ou tente novamente mais tarde.")

# Teste unitário básico
if __name__ == "__main__":
    pgn = """[Event "?\"]\n[Site "?\"]\n[Date "????.??.??"]\n[Round "?\"]\n[White "?\"]\n[Black "?\"]\n[Result "*"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *"""
    result = parse_pgn(pgn)
    for state in result:
        print(state)
