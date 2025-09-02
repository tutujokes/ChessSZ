import chess
import chess.polyglot
import os
import csv
from .trie import OpeningTrie

# Cache global para o Trie de aberturas
_opening_trie = None

def load_lichess_openings():
    """
    Carrega as aberturas dos arquivos TSV e constrói o Trie.
    Retorna o Trie para busca rápida.
    """
    global _opening_trie
    if _opening_trie is not None:
        return _opening_trie
    
    _opening_trie = OpeningTrie()
    tsv_folder = os.path.join(os.path.dirname(__file__), "..", "tsv")
    
    print("DEBUG: Carregando aberturas no Trie...")
    total_loaded = 0
    
    for file_name in ["a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv"]:
        file_path = os.path.join(tsv_folder, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter='\t')
                    for row in reader:
                        if len(row) >= 3:
                            eco_code, opening_name, moves = row[0], row[1], row[2]
                            _opening_trie.insert(moves, eco_code, opening_name)
                            total_loaded += 1
            except Exception as e:
                print(f"DEBUG: Erro ao carregar {file_name}: {e}")
                continue
    
    stats = _opening_trie.get_stats()
    print(f"DEBUG: Trie carregado - {total_loaded} aberturas, {stats['total_nodes']} nós")
    
    return _opening_trie

def get_opening_from_sequence(moves_sequence):
    """
    Busca abertura baseada na sequência completa de lances usando Trie.
    
    Args:
        moves_sequence (list): Lista de movimentos SAN ["e4", "e6", "d4", "d5"]
    
    Returns:
        dict: {'eco': 'C11', 'name': 'French Defense: Classical Variation'} ou None
    """
    if not moves_sequence:
        return None
    
    trie = load_lichess_openings()
    result = trie.search(moves_sequence)
    
    if result:
        eco_code, opening_name = result
        print(f"DEBUG: Abertura encontrada - {eco_code}: {opening_name} para {moves_sequence}")
        return {
            'eco': eco_code,
            'name': opening_name
        }
    
    print(f"DEBUG: Nenhuma abertura encontrada para {moves_sequence}")
    return None

def detect_opening_info(moves_sequence):
    """
    Detecta informações da abertura para a sequência completa de lances.
    Retorna dict com eco, name, ou None se não encontrar.
    """
    return get_opening_from_sequence(moves_sequence)

def classify_opening(prev_fen, played_move, eco_book=None, full_game_moves=None):
    """
    Classifica o lance como Livro se for abertura conhecida NA SEQUÊNCIA CORRETA.
    Retorna uma string ou None.
    """
    # Primeiro tenta Lichess openings com sequência completa usando Trie
    if full_game_moves:
        try:
            trie = load_lichess_openings()
            current_sequence = full_game_moves[:]
            
            # Verifica se a sequência atual é EXATAMENTE uma abertura conhecida
            opening = trie.search_exact(current_sequence)
            if opening:
                return "Livro"
            
            # Se não é uma abertura exata, verifica se existe alguma abertura 
            # que contenha a sequência atual como prefixo
            # Para isso, verifica se existe pelo menos uma abertura mais longa
            # que comece com esta sequência
            
            # Navega pela árvore até onde conseguir
            node = trie
            for move in current_sequence:
                if move not in node.children:
                    return None  # Sequência não existe na árvore
                node = node.children[move]
            
            # Se chegou aqui, a sequência existe na árvore
            # Verifica se há pelo menos um filho (abertura mais longa)
            if node.children:
                return "Livro"  # É prefixo de alguma abertura
            else:
                return None  # Não é prefixo de nenhuma abertura
                        
        except Exception as e:
            print(f"DEBUG: Erro na classificação de abertura: {e}")
            pass
    
    # Fallback para Polyglot
    board = chess.Board(prev_fen if prev_fen else chess.STARTING_FEN)
    if eco_book is None:
        eco_book = os.path.join(os.path.dirname(__file__), "..", "Cerebellum3Merge.bin")
    if eco_book and os.path.exists(eco_book):
        try:
            with chess.polyglot.open_reader(eco_book) as reader:
                for entry in reader.find_all(board):
                    move_san = board.san(entry.move)
                    if played_move == move_san:
                        return "Livro"
        except Exception:
            pass
    return None
