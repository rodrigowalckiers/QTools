### 🏭 QTools Sistema de Qualidade e Gestão v0.1.5 - Automação & Inspeção de Peças 📊 ### 

### 🔧 Funcionalidades:
        ✅ Dashboard em tempo real
        ✅ Gestão completa de usuários & Peças
        ✅ Visualização de Caixas
        ✅ Hierarquia de permissões (Operador/Supervisor/Admin)
        ✅ Remoção rápida com botão na listagem (Supervisor/Admin)
        ✅ Relatórios com exportação em PDF e filtros por data e usuário(Admin)
        ✅ Configurações de Metas e Critérios
        ✅ Logs para auditoria
        ✅ Timeout de sessão automático
        ✅ Backup automático

### 🔜 Próxima Release v.0.1.6:
        ⚠️ Configurações do Sistema
        ⚠️ Filtros por data em todas as telas
        ⚠️ Tela para análise da auditoria e logs
        ⚠️ Correção erro backups, centralização da tela


### 🚀 Como Rodar o Programa
        📦 Pré-requisitos

        Python 3.8 ou superior instalado
        Sistema operacional: Windows, Linux ou macOS

### 📥 Instalação & Execução
        Opção 1: Instalação Automática (Recomendado)
        O programa instala automaticamente todas as dependências na primeira execução.
        # 1. Baixe o código ou faça o clone do repositório
            https://github.com/rodrigowalckiers/QTools.git

        # 2. Navegue até a pasta do arquivo
            cd caminho/para/a/pasta

        # 3. Execute o programa
            Inicializadores: Clique em start_windows.bat ou start_linux.sh
            Bash: python nome_do_arquivo.py

⚠️ **OBS** Na primeira execução, o sistema criará a pasta data e instalará automaticamente:      
                -customtkinter (interface gráfica)
                -Pillow (processamento de imagens)
                -bcrypt (criptografia de senhas)
                -matplotlib (gráficos)
                -reportlab (geração de PDFs)
            Após a instalação, o programa executará

            # Instalação Manual De Dependências
                pip install customtkinter Pillow bcrypt matplotlib reportlab tkcalendar


### 🔐 Primeiro Acesso
    **Credenciais padrão:**
    -Usuário: admin
    -Senha: admin

⚠️ **Recomendação:** Altere a senha padrão após o primeiro login!

---

## 📖 Guia de Uso Passo a Passo

### 1️⃣ Login no Sistema

1. Execute o programa
2. Digite as credenciais (admin/admin na primeira vez)
3. Clique em **"Entrar no Sistema"**

### 2️⃣ Cadastrar Nova Peça

1. No menu principal, clique em **"📝 Cadastrar Nova Peça"**
2. Preencha os dados:
   - **ID da Peça:** código único (ex: PECA001)
   - **Peso:** valor em gramas (ex: 100.5)
   - **Cor:** selecione no menu (azul, verde, etc.)
   - **Comprimento:** valor em centímetros (ex: 15.0)
3. Clique em **"✅ Cadastrar"**
4. O sistema validará automaticamente e informará se foi aprovada ou reprovada

### 3️⃣ Listar Peças

1. Clique em **"📋 Listar Peças"**
2. Use as abas:
   - **"✅ Aprovadas":** peças que passaram no controle
   - **"❌ Reprovadas":** peças que falharam
3. Administradores/Supervisores podem excluir peças diretamente da lista

### 4️⃣ Gerenciar Peças (CRUD - Admin)

1. Clique em **"🔧 Gerenciar Peças (CRUD)"**
2. Digite o ID da peça para buscar
3. Clique em **"Buscar"**
4. Opções disponíveis:
   - **💾 Salvar:** altera os dados (peso, cor, comprimento)
   - **🗑️ Excluir:** remove a peça
   - **🔙 Cancelar:** volta ao menu

### 5️⃣ Gerar Relatórios (Admin)

1. Clique em **"📊 Relatórios Avançados"**
2. Escolha o tipo:
   - **📅 Diário:** selecione uma data
   - **👤 Por Usuário:** selecione o usuário
   - **🔗 Combinado:** selecione data + usuário
3. Clique em **"Gerar Relatório"**
4. Para exportar: **"📄 Exportar PDF"**

### 6️⃣ Gestão de Usuários (Admin)

1. Clique em **"👥 Gestão de Usuários"**
2. Operações:
   - **➕ Novo Usuário:** criar novo usuário
   - **📝 Editar:** alterar dados/nível de acesso
   - **❌ Excluir:** remover usuário (exceto admin)
3. Filtre por tipo: ativos, inativos, nível de acesso

### 7️⃣ Configurações (Admin)

1. Clique em **"⚙️ Configurações"**
2. Abas disponíveis:
   - **🎯 Critérios:** ajuste os limites de qualidade
   - **⚙️ Sistema:** capacidade de caixas, backups (Em desenvolvimento, apenas parte gráfica)
   - **📊 Metas:** metas diárias e alertas

---

## 💡 Exemplos de Uso

### Exemplo 1: Cadastro de Peça Aprovada

**Entrada:**
```
ID: PECA001
Peso: 100.0g
Cor: azul
Comprimento: 15.0cm
```

**Saída:**
```
✅ Peça Aprovada!
Peça PECA001 APROVADA!

- Caixa #1
- Vagas: 9
- Turno: Manhã
```

### Exemplo 2: Cadastro de Peça Reprovada

**Entrada:**
```
ID: PECA002
Peso: 85.0g
Cor: vermelho
Comprimento: 25.0cm
```

**Saída:**
```
❌ Peça Reprovada
Peça PECA002 REPROVADA!

Motivos:
- Peso: 85.0g (esperado: 95-105g)
- Cor: vermelho (esperado: azul, verde)
- Comprimento: 25.0cm (esperado: 10-20cm)
```

### Exemplo 3: Relatório Diário

**Entrada:**
```
Data: 18/11/2025
```

**Saída (Resumo):**
```
📈 RESUMO ESTATÍSTICO
----------------------------------------
- Total de Peças Inspecionadas: 50
- ✅ Aprovadas: 45
- ❌ Reprovadas: 5
- 📊 Taxa de Aprovação: 90.0%

👤 DESEMPENHO POR USUÁRIO
----------------------------------------
- admin: 30 aprov., 3 reprov. (90.9%)
- joao.silva: 15 aprov., 2 reprov. (88.2%)

🕒 ANÁLISE POR TURNO
----------------------------------------
- Manhã: 25 peças (92% aprovação)
- Tarde: 15 peças (86.7% aprovação)
- Noite: 10 peças (90% aprovação)
```

### Exemplo 4: Edição de Peça

**Entrada:**
```
Buscar ID: PECA001
Novo Peso: 102.0g
Nova Cor: verde
Novo Comprimento: 14.5cm
```

**Saída:**
```
✅ Peça editada com sucesso
Peça PECA001 foi atualizada e revalidada.
Status: APROVADA
```

---

### ⚙️ Configurações Padrão
    Critérios de Qualidade:
        Peso: 95g - 105g
        Cores aceitas: azul, verde
        Comprimento: 10cm - 20cm

    Sistema:
        Capacidade da caixa: 10 peças
        Backup automático: Ativado
        Intervalo de backup: 24 horas
        Timeout de sessão: 30 minutos

    Metas:
        Meta diária: 500 peças aprovadas
        Taxa de aprovação mínima: 85%
        Alerta de reprovação alta: 15%

### 🛠️ Solução de Problemas
    Erro: "ModuleNotFoundError"
    Solução: Execute novamente o programa. Ele instalará as dependências automaticamente.
    ---
    Erro: "Permissão negada"
    Solução: Execute o terminal/prompt como administrador.
    --
    Interface não aparece
    Solução: Verifique se o Python 3.8+ está instalado: python --version
    ---
    Dados não são salvos
    Solução: Verifique se a pasta data/ tem permissão de escrita.

### 📝 Notas Importantes
⚠️ **Backup**: O sistema faz backups automáticos, mas recomenda-se copiar a pasta data/ periodicamente
🔐 **Segurança**: Senhas são criptografadas com bcrypt (não são armazenadas em texto puro)
📊 **Auditoria**: Todas as ações são registradas para rastreabilidade
🎨 **Interface**: Otimizada para resoluções de 1000x700 ou superior


### 📄 Versão
QTools Sistema de Qualidade e Gestão v0.1.5

### ⚠️ Suporte
    Para dúvidas ou problemas:
        Verifique este README
        Consulte os logs em data/logs/
        Revise o arquivo de auditoria: data/auditoria.json


### ✨DESENVOLVIDO POR
👨‍💻 **Rodrigo Walckiers**

### PARA
🏭 **Faculdade UniFECAF**


### OPEN SOURCE - GNU LICENSE ###
    