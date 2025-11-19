from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from controller.PecaController import PecaController

class CaixaController:
    """Representa uma caixa"""
    
    def __init__(self, numero: int, capacidade: int = 10):
        self.numero = numero
        self.capacidade = capacidade
        self.pecas: List[PecaController] = []
        self.data_fechamento = None
        self.usuario_fechamento = ""
        self.data_criacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def adicionar_peca(self, peca: PecaController) -> bool:
        """Adiciona peça à caixa"""
        if len(self.pecas) < self.capacidade:
            self.pecas.append(peca)
            if len(self.pecas) >= self.capacidade:
                self.fechar(peca.usuario)
            return True
        return False
    
    def fechar(self, usuario: str = ""):
        """Fecha caixa"""
        self.data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.usuario_fechamento = usuario
    
    def esta_cheia(self) -> bool:
        return len(self.pecas) >= self.capacidade
    
    def vagas_disponiveis(self) -> int:
        return max(0, self.capacidade - len(self.pecas))
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'numero': self.numero,
            'capacidade': self.capacidade,
            'pecas': [p.to_dict() for p in self.pecas],
            'data_fechamento': self.data_fechamento,
            'usuario_fechamento': self.usuario_fechamento,
            'data_criacao': self.data_criacao,
            'quantidade_pecas': len(self.pecas),
            'percentual_cheio': (len(self.pecas) / self.capacidade) * 100
        }