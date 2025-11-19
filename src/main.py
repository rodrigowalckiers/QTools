"""
QTools Sistema de Qualidade e Gestão 
Versão 0.1.5
"""

# ====================================================================================
# VERIFICAÇÃO DE DEPENDÊNCIAS
# ====================================================================================

try:
    import subprocess
    import sys
    import bcrypt
    import customtkinter as ctk
    from tkinter import messagebox
    import matplotlib.pyplot as plt
    from reportlab.lib.pagesizes import A4
except ImportError as e:
    print(f"❌ Erro ao importar dependências: {e}")
    print("⏳ Instalando dependências necessárias...")
    
    # Instalar todas as dependências necessárias
    packages = ["customtkinter", "Pillow", "bcrypt", "matplotlib", "reportlab"]
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado com sucesso")
        except subprocess.CalledProcessError:
                print(f"⚠️ Erro ao instalar {package}, sem este pacote o sistema não funcionará.")

# ====================================================================================
# CONFIGURAÇÃO DO SISTEMA
# ====================================================================================
from core.ConfiguracaoSistema import ConfiguracaoSistema

# ====================================================================================
# APLICAÇÃO PRINCIPAL
# ====================================================================================
from app import Aplicacao

# ====================================================================================
# PONTO DE ENTRADA
# ====================================================================================
def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  🏭 QTools - Sistema de Qualidade e Gestão v0.1.5")
    print("  📊 Automação de Inspeção de Peças")
    print("  ✨ Desenvolvido por: Rodrigo Walckiers")
    print("="*70 + "\n")
    
    print("🔧 Funcionalidades:")
    print("  ✅ Dashboard em tempo real")
    print("  ✅ Gestão completa de usuários & Peças")
    print("  ✅ Visualização de Caixas")
    print("  ✅ Hierarquia de permissões (Operador/Supervisor/Admin)")
    print("  ✅ Remoção rápida com botão na listagem (Supervisor/Admin)")
    print("  ✅ Relatórios com exportação em PDF e filtros por data e usuário(Admin)")
    print("  ✅ Configurações de Metas e Critérios")
    print("  ✅ Logs para auditoria")
    print("  ✅ Timeout de sessão automático")
    print("  ✅ Backup automático")
    print("\n" + "="*70 + "\n")
    
    print("🔜 Próxima Release v.0.1.6:")
    print("  ⚠️ Configurações do Sistema")
    print("  ⚠️ Filtros por data em todas as telas")
    print("  ⚠️ Tela para análise da auditoria e logs")
    print("  ⚠️ Correção erro backups, centralização da tela")
    print("\n" + "="*70 + "\n")
    

    
    try:
        app = Aplicacao()
        app.executar()
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        messagebox.showerror("Erro Fatal", f"Erro crítico:\n\n{str(e)}")
    finally:
        ConfiguracaoSistema.registrar_log("Aplicação encerrada", "SISTEMA")

if __name__ == "__main__":
    main()