from core.ConfiguracaoSistema import ConfiguracaoSistema
from controller.PecaController import PecaController
from controller.CaixaController import CaixaController
from typing import List, Dict, Optional, Tuple
from collections import Counter
import threading
from datetime import datetime, timedelta
import json

# ====================================================================================
# BANCO DE DADOS
# ====================================================================================
class BancoDados:
    """Gerencia dados do sistema"""
    
    def __init__(self):
        self.arquivo_pecas = ConfiguracaoSistema.ARQUIVO_PECAS
        self.arquivo_caixas = ConfiguracaoSistema.ARQUIVO_CAIXAS
        self.config = ConfiguracaoSistema.carregar_configuracao()
        self.pecas_aprovadas: List[PecaController] = []
        self.pecas_reprovadas: List[PecaController] = []
        self.caixas_fechadas: List[CaixaController] = []
        
        capacidade = self.config.get('capacidade_caixa', 10)
        self.caixa_atual: CaixaController = CaixaController(1, capacidade)
        
        self.carregar_dados()
        self.iniciar_backup_automatico()
    
    def carregar_dados(self):
        """Carrega dados dos arquivos"""
        if self.arquivo_pecas.exists():
            try:
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                self.pecas_aprovadas.clear()
                self.pecas_reprovadas.clear()
                
                for p_dict in dados.get('aprovadas', []):
                    peca = PecaController(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_aprovadas.append(peca)
                
                for p_dict in dados.get('reprovadas', []):
                    peca = PecaController(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.motivos_reprovacao = p_dict.get('motivos_reprovacao', [])
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.pecas_reprovadas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar peças: {e}", "ERRO")
        
        if self.arquivo_caixas.exists():
            try:
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                self.caixas_fechadas.clear()
                
                for c_dict in dados.get('fechadas', []):
                    capacidade = c_dict.get('capacidade', self.config.get('capacidade_caixa', 10))
                    caixa = CaixaController(c_dict['numero'], capacidade)
                    caixa.data_fechamento = c_dict.get('data_fechamento')
                    caixa.usuario_fechamento = c_dict.get('usuario_fechamento', '')
                    caixa.data_criacao = c_dict.get('data_criacao', '')
                    
                    for p_dict in c_dict.get('pecas', []):
                        peca = PecaController(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                        peca.aprovada = p_dict['aprovada']
                        peca.timestamp = p_dict.get('timestamp', '')
                        peca.data_inspecao = p_dict.get('data_inspecao', '')
                        peca.turno = p_dict.get('turno', '')
                        caixa.pecas.append(peca)
                    self.caixas_fechadas.append(caixa)
                
                c_atual = dados.get('atual', {})
                capacidade_atual = c_atual.get('capacidade', self.config.get('capacidade_caixa', 10))
                self.caixa_atual = CaixaController(c_atual.get('numero', len(self.caixas_fechadas) + 1), capacidade_atual)
                
                for p_dict in c_atual.get('pecas', []):
                    peca = PecaController(p_dict['id'], p_dict['peso'], p_dict['cor'], p_dict['comprimento'], p_dict.get('usuario', ''))
                    peca.aprovada = p_dict['aprovada']
                    peca.timestamp = p_dict.get('timestamp', '')
                    peca.data_inspecao = p_dict.get('data_inspecao', '')
                    peca.turno = p_dict.get('turno', '')
                    self.caixa_atual.pecas.append(peca)
            except Exception as e:
                ConfiguracaoSistema.registrar_log(f"Erro ao carregar caixas: {e}", "ERRO")
    
    def salvar_dados(self):
        """Salva dados"""
        try:
            self.fazer_backup()
            
            dados_pecas = {
                'aprovadas': [p.to_dict() for p in self.pecas_aprovadas],
                'reprovadas': [p.to_dict() for p in self.pecas_reprovadas],
                'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.arquivo_pecas, 'w', encoding='utf-8') as f:
                json.dump(dados_pecas, f, indent=2, ensure_ascii=False)
            
            dados_caixas = {
                'fechadas': [c.to_dict() for c in self.caixas_fechadas],
                'atual': self.caixa_atual.to_dict(),
                'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.arquivo_caixas, 'w', encoding='utf-8') as f:
                json.dump(dados_caixas, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao salvar: {e}", "ERRO")
            return False
    
    def fazer_backup(self):
        """Faz backup"""
        try:
            if not self.config.get('auto_backup', True):
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.arquivo_pecas.exists():
                backup_pecas = ConfiguracaoSistema.BACKUP_DIR / f"pecas_backup_{timestamp}.json"
                with open(self.arquivo_pecas, 'r', encoding='utf-8') as origem:
                    with open(backup_pecas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
            
            if self.arquivo_caixas.exists():
                backup_caixas = ConfiguracaoSistema.BACKUP_DIR / f"caixas_backup_{timestamp}.json"
                with open(self.arquivo_caixas, 'r', encoding='utf-8') as origem:
                    with open(backup_caixas, 'w', encoding='utf-8') as destino:
                        destino.write(origem.read())
                        
            ConfiguracaoSistema.registrar_log("Backup realizado", "BACKUP")
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro backup: {e}", "ERRO")
    
    def iniciar_backup_automatico(self):
        """Inicia thread de backup automático"""
        def backup_thread():
            while True:
                try:
                    ultimo_backup = getattr(self, '_ultimo_backup', None)
                    intervalo_horas = self.config.get('backup_interval_hours', 24)
                    
                    if not ultimo_backup or (datetime.now() - ultimo_backup) > timedelta(hours=intervalo_horas):
                        self.fazer_backup()
                        self._ultimo_backup = datetime.now()
                    
                    threading.Event().wait(3600)
                except:
                    pass
        
        if self.config.get('auto_backup', True):
            thread = threading.Thread(target=backup_thread, daemon=True)
            thread.start()
    
    def adicionar_peca(self, peca: PecaController) -> Tuple[bool, str]:
        """Adiciona peça"""
        try:
            for p in self.pecas_aprovadas + self.pecas_reprovadas:
                if p.id_peca == peca.id_peca:
                    return False, f"ID {peca.id_peca} já existe"
            
            criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
            peca.validar(criterios)
            
            if peca.aprovada:
                self.pecas_aprovadas.append(peca)
                
                if not self.caixa_atual.adicionar_peca(peca):
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = CaixaController(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
                    self.caixa_atual.adicionar_peca(peca)
                
                if self.caixa_atual.esta_cheia():
                    self.caixas_fechadas.append(self.caixa_atual)
                    self.caixa_atual = CaixaController(len(self.caixas_fechadas) + 1, self.config.get('capacidade_caixa', 10))
            else:
                self.pecas_reprovadas.append(peca)
            
            self.salvar_dados()
            ConfiguracaoSistema.registrar_log(f"Peça {peca.id_peca} {'aprovada' if peca.aprovada else 'reprovada'}", "INSPECAO")
            
            return True, "Peça adicionada"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def editar_peca(self, id_peca: str, novo_peso: float, nova_cor: str, novo_comprimento: float, usuario: str = "") -> Tuple[bool, str]:
        """Edita uma peça existente"""
        try:
            id_peca = id_peca.upper().strip()
            
            # Buscar em peças aprovadas
            for peca in self.pecas_aprovadas:
                if peca.id_peca == id_peca:
                    peca_antiga = peca.to_dict().copy()
                    
                    peca.peso = novo_peso
                    peca.cor = nova_cor.lower()
                    peca.comprimento = novo_comprimento
                    
                    # Revalidar a peça
                    criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
                    estava_aprovada = peca.aprovada
                    peca.validar(criterios)
                    
                    # Se foi reprovada após edição, mover para lista de reprovadas
                    if not peca.aprovada and estava_aprovada:
                        self.pecas_aprovadas.remove(peca)
                        self.pecas_reprovadas.append(peca)
                        # Remover da caixa atual se estiver lá
                        for p_caixa in self.caixa_atual.pecas:
                            if p_caixa.id_peca == id_peca:
                                self.caixa_atual.pecas.remove(p_caixa)
                                break
                    
                    self.salvar_dados()
                    ConfiguracaoSistema.registrar_auditoria(usuario, "EDITAR_PECA", 
                        f"ID: {id_peca} - De: Peso{peca_antiga['peso']}g, Cor{peca_antiga['cor']}, Comp{peca_antiga['comprimento']}cm | Para: Peso{novo_peso}g, Cor{nova_cor}, Comp{novo_comprimento}cm")
                    
                    return True, "Peça editada com sucesso"
            
            # Buscar em peças reprovadas
            for peca in self.pecas_reprovadas:
                if peca.id_peca == id_peca:
                    peca_antiga = peca.to_dict().copy()
                    
                    peca.peso = novo_peso
                    peca.cor = nova_cor.lower()
                    peca.comprimento = novo_comprimento
                    
                    # Revalidar a peça
                    criterios = self.config.get('criterios_qualidade', ConfiguracaoSistema.CONFIG_PADRAO['criterios_qualidade'])
                    estava_aprovada = peca.aprovada
                    peca.validar(criterios)
                    
                    # Se foi aprovada após edição, mover para lista de aprovadas
                    if peca.aprovada and not estava_aprovada:
                        self.pecas_reprovadas.remove(peca)
                        self.pecas_aprovadas.append(peca)
                        # Adicionar à caixa atual
                        self.caixa_atual.adicionar_peca(peca)
                    
                    self.salvar_dados()
                    ConfiguracaoSistema.registrar_auditoria(usuario, "EDITAR_PECA", 
                        f"ID: {id_peca} - De: Peso{peca_antiga['peso']}g, Cor{peca_antiga['cor']}, Comp{peca_antiga['comprimento']}cm | Para: Peso{novo_peso}g, Cor{nova_cor}, Comp{novo_comprimento}cm")
                    
                    return True, "Peça editada com sucesso"
            
            return False, f"Peça {id_peca} não encontrada"
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao editar peça: {e}", "ERRO")
            return False, f"Erro interno: {str(e)}"
    
    def remover_peca(self, id_peca: str, usuario: str = "", justificativa: str = "") -> Tuple[bool, str]:
        """Remove peça"""
        id_peca = id_peca.upper().strip()
        
        for i, peca in enumerate(self.pecas_aprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_aprovadas[i]
                
                for j, p_caixa in enumerate(self.caixa_atual.pecas):
                    if p_caixa.id_peca == id_peca:
                        del self.caixa_atual.pecas[j]
                        break
                
                self.salvar_dados()
                ConfiguracaoSistema.registrar_auditoria(usuario, "REMOVER_PECA", f"ID: {id_peca} - {justificativa}")
                return True, f"Peça {id_peca} removida"
        
        for i, peca in enumerate(self.pecas_reprovadas):
            if peca.id_peca == id_peca:
                del self.pecas_reprovadas[i]
                self.salvar_dados()
                ConfiguracaoSistema.registrar_auditoria(usuario, "REMOVER_PECA", f"ID: {id_peca} - {justificativa}")
                return True, f"Peça {id_peca} removida"
        
        return False, f"Peça {id_peca} não encontrada"
    
    # ========== NOVOS MÉTODOS DE FILTRO ==========
    def filtrar_pecas_por_data(self, pecas: List[PecaController], data_inicio: str = None, data_fim: str = None) -> List[PecaController]:
        """Filtra peças por período"""
        if not data_inicio and not data_fim:
            return pecas
        
        pecas_filtradas = []
        for peca in pecas:
            try:
                data_peca = datetime.strptime(peca.timestamp, "%Y-%m-%d %H:%M:%S")
                
                if data_inicio:
                    dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
                    if data_peca < data_inicio:
                        continue
                
                if data_fim:
                    dt_fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
                    if data_peca >= data_fim:
                        continue
                
                pecas_filtradas.append(peca)
            except:
                pass
        
        return pecas_filtradas
    
    def buscar_peca_por_id(self, id_peca: str) -> Optional[PecaController]:
        """Busca peça específica por ID"""
        id_peca = id_peca.upper().strip()
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.id_peca == id_peca:
                return peca
        return None
    
    def buscar_pecas_por_data(self, data: str) -> List[PecaController]:
        """Busca peças por data específica (formato: YYYY-MM-DD)"""
        data = datetime.strftime(data, '%Y-%m-%d')
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.data_inspecao == data:
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def buscar_pecas_por_usuario(self, usuario: str) -> List[PecaController]:
        """Busca peças por usuário específico"""
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.usuario.lower() == usuario.lower():
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def buscar_pecas_por_data_e_usuario(self, data: str, usuario: str) -> List[PecaController]:
        data = datetime.strftime(data, '%Y-%m-%d')
        """Busca peças por data E usuário"""
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            if peca.data_inspecao == data and peca.usuario.lower() == usuario.lower():
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def buscar_pecas_por_periodo(self, data_inicio, data_fim) -> List[PecaController]:
        # data_inicio = datetime.strftime(data_inicio, '%Y-%m-%d')
        # data_fim = datetime.strftime(data_fim, '%Y-%m-%d')
        """Busca peças por período"""
        pecas_filtradas = []
        for peca in self.pecas_aprovadas + self.pecas_reprovadas:
            data_peca = datetime.strptime(peca.data_inspecao, '%Y-%m-%d')
            data_peca = datetime.date(data_peca)
            if data_inicio <= data_peca <= data_fim:
                pecas_filtradas.append(peca)
        return pecas_filtradas
    
    def gerar_relatorio_diario(self, data: datetime) -> Dict:
        """Gera relatório específico para um dia"""
        pecas_dia = self.buscar_pecas_por_data(data)
        return self._gerar_relatorio_estruturado(pecas_dia, f"Relatório Diário - {data}")
    
    def gerar_relatorio_usuario(self, usuario: str, data_inicio: str = None, data_fim: str = None) -> Dict:
        """Gera relatório específico para um usuário"""
        if data_inicio and data_fim:
            todas_pecas = self.buscar_pecas_por_periodo(data_inicio, data_fim)
            pecas_usuario = [p for p in todas_pecas if p.usuario.lower() == usuario.lower()]
        else:
            pecas_usuario = self.buscar_pecas_por_usuario(usuario)
        
        periodo = f"{data_inicio} a {data_fim}" if data_inicio and data_fim else "Todo o período"
        return self._gerar_relatorio_estruturado(pecas_usuario, f"Relatório do Usuário {usuario} - {periodo}")
    
    def gerar_relatorio_diario_usuario(self, data: str, usuario: str) -> Dict:
        """Gera relatório específico para um dia e usuário"""
        pecas = self.buscar_pecas_por_data_e_usuario(data, usuario)
        return self._gerar_relatorio_estruturado(pecas, f"Relatório Diário - {data} - Usuário: {usuario}")
    
    def _gerar_relatorio_estruturado(self, pecas: List[PecaController], titulo: str) -> Dict:
        """Gera estrutura de relatório a partir de uma lista de peças"""
        aprovadas = [p for p in pecas if p.aprovada]
        reprovadas = [p for p in pecas if not p.aprovada]
        
        total_pecas = len(pecas)
        taxa_aprovacao = (len(aprovadas) / total_pecas * 100) if total_pecas > 0 else 0
        
        # Estatísticas por usuário
        estatisticas_usuario = {}
        for peca in pecas:
            usuario = peca.usuario
            if usuario not in estatisticas_usuario:
                estatisticas_usuario[usuario] = {'aprovadas': 0, 'reprovadas': 0, 'total': 0}
            
            if peca.aprovada:
                estatisticas_usuario[usuario]['aprovadas'] += 1
            else:
                estatisticas_usuario[usuario]['reprovadas'] += 1
            estatisticas_usuario[usuario]['total'] += 1
        
        # Estatísticas por turno
        estatisticas_turno = {}
        for peca in pecas:
            turno = peca.turno
            if turno not in estatisticas_turno:
                estatisticas_turno[turno] = {'aprovadas': 0, 'reprovadas': 0, 'total': 0}
            
            if peca.aprovada:
                estatisticas_turno[turno]['aprovadas'] += 1
            else:
                estatisticas_turno[turno]['reprovadas'] += 1
            estatisticas_turno[turno]['total'] += 1
        
        # Análise de motivos de reprovação
        motivos_reprovacao = Counter()
        for peca in reprovadas:
            for motivo in peca.motivos_reprovacao:
                if 'Peso' in motivo:
                    motivos_reprovacao['Peso'] += 1
                elif 'Cor' in motivo:
                    motivos_reprovacao['Cor'] += 1
                elif 'Comprimento' in motivo:
                    motivos_reprovacao['Comprimento'] += 1
        
        return {
            'titulo': titulo,
            'data_geracao': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_pecas_aprovadas': len(aprovadas),
            'total_pecas_reprovadas': len(reprovadas),
            'total_pecas_inspecionadas': total_pecas,
            'taxa_aprovacao': round(taxa_aprovacao, 2),
            'estatisticas_usuario': estatisticas_usuario,
            'estatisticas_turno': estatisticas_turno,
            'analise_motivos_reprovacao': dict(motivos_reprovacao),
            'pecas_detalhadas': [p.to_dict() for p in pecas]
        }