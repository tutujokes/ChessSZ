import os
import csv
import chess
import chess.pgn
from io import StringIO

# Cache global para o mapeamento FEN → Abertura
_fen_to_opening = None

def load_fen_openings():
    """
    Carrega e retorna o mapeamento FEN → (ECO, Nome da Abertura).
    Usa cache global para evitar recarregar.
    """
    global _fen_to_opening
    
    if _fen_to_opening is not None:
        return _fen_to_opening
    
    print("DEBUG: Carregando mapeamento FEN → Abertura...")
    _fen_to_opening = {}
    total_loaded = 0
    
    # Pasta dos arquivos TSV
    tsv_folder = os.path.join(os.path.dirname(__file__), "..", "tsv")
    
    for file_name in ["a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv"]:
        file_path = os.path.join(tsv_folder, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter='\t')
                    for row in reader:
                        if len(row) >= 3:
                            eco_code, opening_name, moves = row[0], row[1], row[2]
                            
                            # Converte a sequência de movimentos para FEN final
                            fen = moves_to_fen(moves)
                            if fen:
                                _fen_to_opening[fen] = (eco_code, opening_name)
                                total_loaded += 1
                                
            except Exception as e:
                print(f"DEBUG: Erro ao carregar {file_name}: {e}")
                continue
    
    print(f"DEBUG: FEN mapping carregado - {total_loaded} posições")
    return _fen_to_opening

def moves_to_fen(moves_string):
    """
    Converte uma string de movimentos (ex: "1. e4 e6 2. d4 d5") para FEN final.
    
    Args:
        moves_string (str): String com os movimentos
    
    Returns:
        str: FEN da posição final ou None se erro
    """
    try:
        # Cria um jogo falso para processar os movimentos
        pgn_text = f"[Event \"\"]\n[Site \"\"]\n[Date \"\"]\n[Round \"\"]\n[White \"\"]\n[Black \"\"]\n[Result \"*\"]\n\n{moves_string} *"
        game = chess.pgn.read_game(StringIO(pgn_text))
        
        if game is None:
            return None
            
        # Executa todos os movimentos
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        
        return board.fen()
        
    except Exception as e:
        print(f"DEBUG: Erro ao converter movimentos '{moves_string}' para FEN: {e}")
        return None

def normalize_fen(fen):
    """
    Normaliza um FEN removendo os contadores de movimento para comparação.
    Mantém apenas: posição, turno, castling e en passant.
    """
    parts = fen.split()
    if len(parts) >= 4:
        # Remove half-move e full-move counters, mantém apenas os primeiros 4 campos
        return ' '.join(parts[:4])
    return fen

def get_opening_by_fen(fen):
    """
    Busca uma abertura pelo FEN da posição.
    
    Args:
        fen (str): FEN da posição
    
    Returns:
        tuple: (eco_code, opening_name) ou None se não encontrar
    """
    fen_map = load_fen_openings()
    
    # Primeiro tenta busca exata
    if fen in fen_map:
        return fen_map[fen]
    
    # Se não encontrar, tenta busca normalizada (ignorando contadores)
    normalized_fen = normalize_fen(fen)
    for stored_fen, opening in fen_map.items():
        if normalize_fen(stored_fen) == normalized_fen:
            return opening
    
    return None

def classify_move_by_fen(current_fen, move_number=None):
    """
    Classifica um movimento como "Livro" se a posição atual existe nas aberturas.
    Para os primeiros movimentos, é mais flexível se não encontrar a posição exata.
    
    Args:
        current_fen (str): FEN da posição após o movimento
        move_number (int): Número do movimento (opcional, para lógica de fallback)
    
    Returns:
        str: "Livro" se a posição é teórica, None caso contrário
    """
    opening = get_opening_by_fen(current_fen)
    if opening:
        return "Livro"
    
    # Fallback: se estivermos nos primeiros 8-10 movimentos e a posição parece de abertura,
    # ainda pode ser considerado teoria mesmo que não esteja no banco exato
    if move_number and move_number <= 10:
        # Verifica se a posição tem características de abertura
        if is_likely_opening_position(current_fen):
            return "Livro"
    
    return None

def is_likely_opening_position(fen):
    """
    Verifica se uma posição FEN parece ser de abertura baseado em heurísticas simples.
    
    Args:
        fen (str): FEN da posição
        
    Returns:
        bool: True se parece posição de abertura
    """
    try:
        import chess
        board = chess.Board(fen)
        
        # Heurísticas para identificar posição de abertura:
        # 1. Poucas peças foram movidas
        # 2. Reis ainda não fizeram roque
        # 3. Maioria das peças ainda na posição inicial
        
        piece_count = len(board.piece_map())
        
        # Se ainda temos quase todas as peças (32 ou próximo), provavelmente é abertura
        if piece_count >= 30:
            return True
            
        return False
        
    except Exception:
        return False

def detect_opening_info_by_fen(final_fen, all_fens=None):
    """
    Detecta informações da abertura baseado no FEN final.
    Se não encontrar pela posição final, tenta pelas posições anteriores.
    Retorna dict com eco, name, ou None se não encontrar.
    """
    print(f"DEBUG: detect_opening_info_by_fen chamada com FEN completo: '{final_fen}'")
    
    # Primeiro tenta pela posição final
    opening = get_opening_by_fen(final_fen)
    if opening:
        eco_code, opening_name = opening
        print(f"DEBUG: Abertura encontrada por FEN final - {eco_code}: {opening_name}")
        return {
            'eco': eco_code,
            'name': opening_name
        }
    
    # Se não encontrou e temos todas as posições, tenta pelas anteriores (da mais recente para a mais antiga)
    if all_fens:
        print(f"DEBUG: Tentando detectar abertura pelas {len(all_fens)} posições anteriores...")
        for i, fen in enumerate(reversed(all_fens[:-1])):  # Exclui a última (que já testamos)
            opening = get_opening_by_fen(fen)
            if opening:
                eco_code, opening_name = opening
                print(f"DEBUG: Abertura encontrada pela posição {len(all_fens)-i-1} - {eco_code}: {opening_name}")
                return {
                    'eco': eco_code,
                    'name': opening_name
                }
    
    print(f"DEBUG: Nenhuma abertura encontrada para nenhuma posição")
    return None
