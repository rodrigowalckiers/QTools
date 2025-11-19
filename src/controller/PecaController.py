from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# ====================================================================================
# PEÇA CONTROLLER
# ====================================================================================
class PecaController:
    """Representa uma peça"""
    
    def __init__(self, id_peca: str, peso: float, cor: str, comprimento: float, usuario: str = ""):
        self.id_peca = id_peca.upper().strip()
        self.peso = peso
        self.cor = cor.lower().strip()
        self.comprimento = comprimento
        self.usuario = usuario
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data_inspecao = datetime.now().strftime("%Y-%m-%d")
        self.aprovada = False
        self.motivos_reprovacao = []
        self.turno = self.obter_turno_atual()
        
    def obter_turno_atual(self) -> str:
        """Determina turno"""
        hora = datetime.now().hour
        if 6 <= hora < 14:
            return "Manhã"
        elif 14 <= hora < 22:
            return "Tarde"
        else:
            return "Noite"
    
    def validar(self, criterios: Dict) -> bool:
        """Valida peça"""
        self.motivos_reprovacao = []
        
        if not (criterios['peso_min'] <= self.peso <= criterios['peso_max']):
            self.motivos_reprovacao.append(
                f"Peso: {self.peso}g (esperado: {criterios['peso_min']}-{criterios['peso_max']}g)"
            )
        
        if self.cor not in criterios['cores_aceitas']:
            cores = ", ".join(criterios['cores_aceitas'])
            self.motivos_reprovacao.append(f"Cor: {self.cor} (esperado: {cores})")
        
        if not (criterios['comprimento_min'] <= self.comprimento <= criterios['comprimento_max']):
            self.motivos_reprovacao.append(
                f"Comprimento: {self.comprimento}cm (esperado: {criterios['comprimento_min']}-{criterios['comprimento_max']}cm)"
            )
        
        self.aprovada = len(self.motivos_reprovacao) == 0
        return self.aprovada
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id_peca,
            'peso': self.peso,
            'cor': self.cor,
            'comprimento': self.comprimento,
            'usuario': self.usuario,
            'timestamp': self.timestamp,
            'data_inspecao': self.data_inspecao,
            'turno': self.turno,
            'aprovada': self.aprovada,
            'motivos_reprovacao': self.motivos_reprovacao
        }