"""
Trie (Árvore de Prefixos) para busca rápida de aberturas de xadrez.
Complexidade: O(k) onde k = número de movimentos na sequência.
"""

class OpeningTrie:
    def __init__(self):
        self.children = {}
        self.opening_data = None  # (eco_code, opening_name)
    
    def insert(self, moves_sequence, eco_code, opening_name):
        """
        Insere uma abertura no Trie.
        
        Args:
            moves_sequence (str): Sequência de movimentos (ex: "1. e4 e6 2. d4 d5")
            eco_code (str): Código ECO (ex: "C11")
            opening_name (str): Nome da abertura
        """
        # Remove números dos movimentos e normaliza
        moves = self._normalize_moves(moves_sequence)
        
        node = self
        for move in moves:
            if move not in node.children:
                node.children[move] = OpeningTrie()
            node = node.children[move]
        
        # Armazena os dados da abertura no nó final
        node.opening_data = (eco_code, opening_name)
    
    def search(self, moves_sequence):
        """
        Busca a abertura mais longa que corresponde à sequência.
        
        Args:
            moves_sequence (list): Lista de movimentos SAN (ex: ["e4", "e6", "d4"])
        
        Returns:
            tuple: (eco_code, opening_name) ou None se não encontrar
        """
        node = self
        last_found = None
        
        for move in moves_sequence:
            if move not in node.children:
                break
            node = node.children[move]
            
            # Se encontrou uma abertura, armazena (pode haver uma mais longa)
            if node.opening_data:
                last_found = node.opening_data
        
        return last_found
    
    def search_exact(self, moves_sequence):
        """
        Busca uma sequência EXATA de movimentos.
        Só retorna resultado se a sequência completa existir como abertura.
        
        Args:
            moves_sequence (list): Lista de movimentos SAN (ex: ["e4", "e6", "d4"])
        
        Returns:
            tuple: (eco_code, opening_name) ou None se a sequência exata não for uma abertura
        """
        node = self
        
        for move in moves_sequence:
            if move not in node.children:
                return None
            node = node.children[move]
        
        # Só retorna se esta sequência EXATA tem dados de abertura
        return node.opening_data
    
    def _normalize_moves(self, moves_sequence):
        """
        Normaliza a sequência de movimentos removendo números.
        
        Args:
            moves_sequence (str): "1. e4 e6 2. d4 d5 3. Nc3"
        
        Returns:
            list: ["e4", "e6", "d4", "d5", "Nc3"]
        """
        moves = []
        parts = moves_sequence.split()
        
        for part in parts:
            # Pula números dos movimentos (ex: "1.", "2.", etc.)
            if not part.endswith('.') and not part.isdigit():
                moves.append(part)
        
        return moves
    
    def get_stats(self):
        """
        Retorna estatísticas do Trie para debug.
        
        Returns:
            dict: Estatísticas (nodes, openings, etc.)
        """
        def count_nodes(node):
            count = 1
            openings = 1 if node.opening_data else 0
            for child in node.children.values():
                child_count, child_openings = count_nodes(child)
                count += child_count
                openings += child_openings
            return count, openings
        
        total_nodes, total_openings = count_nodes(self)
        return {
            "total_nodes": total_nodes,
            "total_openings": total_openings,
            "root_children": len(self.children)
        }
