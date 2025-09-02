from pydantic import BaseModel, Field
from typing import Optional, List, Literal

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
    missed_win: Optional[bool] = None

class Summary(BaseModel):
    winner: Optional[Literal["white", "black", "draw"]] = None
    avg_depth: int

class OpeningInfo(BaseModel):
    eco: str
    name: str

class AnalyzeResponse(BaseModel):
    opening: Optional[OpeningInfo] = None
    moves: List[Move]
    summary: Summary
