import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================
from core.ConfiguracaoSistema import ConfiguracaoSistema

# ====================================================================================
# GERADOR DE RELATÓRIOS
# ====================================================================================

class Relatorios:
    """Gera relatórios em PDF profissional"""
    
    @staticmethod
    def gerar_relatorio_pdf(relatorio: Dict, caminho: str, usuario: str):
        """Gera Relatório PDF"""
        try:
            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f538d'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("🏭 RELATÓRIO DE CONTROLE DE QUALIDADE", titulo_style))
            story.append(Paragraph(f"Sistema Industrial - Versão 3.1.1", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
            
            # Informações do relatório
            info_data = [
                ['Data de Geração:', relatorio['data_geracao']],
                ['Relatório:', relatorio['titulo']],
                ['Gerado por:', usuario],
            ]
            
            info_table = Table(info_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8e8e8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 1*cm))
            
            # Resumo Executivo
            resumo_style = ParagraphStyle(
                'ResumoTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1f538d'),
                spaceAfter=15
            )
            
            story.append(Paragraph("📈 RESUMO EXECUTIVO", resumo_style))
            
            resumo_data = [
                ['Métrica', 'Valor', 'Status'],
                ['Total de Peças Inspecionadas', f"{relatorio['total_pecas_inspecionadas']:,}", '✓'],
                ['Peças Aprovadas', f"{relatorio['total_pecas_aprovadas']:,}", '✅'],
                ['Peças Reprovadas', f"{relatorio['total_pecas_reprovadas']:,}", '❌'],
                ['Taxa de Aprovação', f"{relatorio['taxa_aprovacao']:.2f}%", 
                 '🟢' if relatorio['taxa_aprovacao'] >= 85 else '🟡' if relatorio['taxa_aprovacao'] >= 70 else '🔴'],
            ]
            
            resumo_table = Table(resumo_data, colWidths=[7*cm, 5*cm, 3*cm])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f538d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(resumo_table)
            story.append(Spacer(1, 1*cm))
            
            # Estatísticas por Usuário
            if relatorio['estatisticas_usuario']:
                story.append(Paragraph("👤 ANÁLISE POR USUÁRIO", resumo_style))
                
                usuario_data = [['Usuário', 'Aprovadas', 'Reprovadas', 'Total', 'Taxa Aprov.']]
                for usuario, stats in relatorio['estatisticas_usuario'].items():
                    taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    usuario_data.append([
                        usuario,
                        str(stats['aprovadas']),
                        str(stats['reprovadas']),
                        str(stats['total']),
                        f"{taxa:.1f}%"
                    ])
                
                usuario_table = Table(usuario_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
                usuario_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(usuario_table)
                story.append(Spacer(1, 0.8*cm))
            
            # Estatísticas por Turno
            if relatorio['estatisticas_turno']:
                story.append(Paragraph("🕒 ANÁLISE POR TURNO", resumo_style))
                
                turno_data = [['Turno', 'Aprovadas', 'Reprovadas', 'Total', 'Taxa Aprov.']]
                for turno, stats in relatorio['estatisticas_turno'].items():
                    taxa = (stats['aprovadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    turno_data.append([
                        turno,
                        str(stats['aprovadas']),
                        str(stats['reprovadas']),
                        str(stats['total']),
                        f"{taxa:.1f}%"
                    ])
                
                turno_table = Table(turno_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
                turno_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(turno_table)
                story.append(Spacer(1, 0.8*cm))
            
            # Análise de Reprovações
            if relatorio['analise_motivos_reprovacao']:
                story.append(Paragraph("❌ ANÁLISE DE MOTIVOS DE REPROVAÇÃO", resumo_style))
                
                motivos_data = [['Motivo', 'Quantidade', 'Percentual']]
                total_reprov = sum(relatorio['analise_motivos_reprovacao'].values())
                
                for motivo, qtd in relatorio['analise_motivos_reprovacao'].items():
                    perc = (qtd / total_reprov * 100) if total_reprov > 0 else 0
                    motivos_data.append([motivo, str(qtd), f"{perc:.1f}%"])
                
                motivos_table = Table(motivos_data, colWidths=[6*cm, 4*cm, 5*cm])
                motivos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                story.append(motivos_table)
                story.append(Spacer(1, 1*cm))
            
            # Rodapé
            story.append(Spacer(1, 2*cm))
            rodape = Paragraph(
                f"Relatório gerado automaticamente - Sistema de Controle de Qualidade v3.1.1<br/>"
                f"© {datetime.now().year} - Todos os direitos reservados",
                styles['Normal']
            )
            story.append(rodape)
            
            # Gerar PDF
            doc.build(story)
            ConfiguracaoSistema.registrar_log(f"Relatório PDF gerado: {caminho}", "RELATORIO")
            return True, caminho
            
        except Exception as e:
            ConfiguracaoSistema.registrar_log(f"Erro ao gerar PDF: {e}", "ERRO")
            return False, f"Erro: {str(e)}"