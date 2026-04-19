# 🚗 Dashboard Financeiro e Comissões Automotivo

Este é um projeto web desenvolvido em Python com **Streamlit** para processamento, análise e projeção de relatórios de ordens de serviço em formato PDF.

## 🌟 Funcionalidades

- Extração automática de dados dos PDFs de Vendas (Cliente, Data, Valores).
- Cálculo automatizado das comissões:
  - **Peças e Serviços:** 2%
  - **Pneus:** 1%
- Gráficos modernos de evolução de vendas e comissões.
- Projeção de Faturamento e Comissão de final de mês via **Machine Learning** (Regressão Linear).
- Tabelas detalhadas para auditoria e histórico de vendas.
- Interface moderna "Dark Mode" para visibilidade premium.

---

## 🚀 Como Executar Localmente

### 1. Requisitos
- Python 3.9+ instalado
- Arquivos de ordem de serviços gerados em PDF

### 2. Instalação
Na raiz do projeto (onde está o arquivo `app.py`), abra um terminal e rode:
```bash
# Criação do ambiente virtual (Recomendado)
python -m venv venv

# Ativação do ambiente
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instalação das dependências
pip install -r requirements.txt
```

### 3. Execução
Com o ambiente ativado, execute:
```bash
streamlit run app.py
```
O navegador se abrirá automaticamente na página web do dashboard.

---

## ☁️ Como Fazer o Deploy para Acessar de Qualquer Dispositivo

O método mais fácil e gratuito para hospedar sua aplicação é através do **Streamlit Community Cloud**. Siga os passos:

### Passo 1: Subir o Código no GitHub
1. Crie uma conta gratuita em [GitHub](https://github.com/);
2. Crie um novo Repositório (pode ser "Privado" se não quiser que vejam seus códigos);
3. Faça o upload dos seguintes arquivos do projeto para o Github:
   - `app.py`
   - O diretório `parser/`
   - O diretório `services/`
   - O diretório `utils/`
   - `requirements.txt`
   - *(Atenção: Não suba a pasta `venv` e nem PDFs de clientes por segurança)*.

### Passo 2: Conectar ao Streamlit Cloud
1. Vá até o [Streamlit Share](https://share.streamlit.io/) e crie uma conta usando seu login do GitHub.
2. Clique no botão **"New app"**.
3. Selecione o repositório que você criou, a branch (ex: `main`), e em "Main file path", digite `app.py`.
4. Clique em **"Deploy!"**.
5. Aguarde o Streamlit instalar as bibliotecas do `requirements.txt`. Uma vez concluído, você terá um link público.

### Conexão com Google Drive Local (Alternativa)
Se preferir não usar hospedagem em nuvem:
1. Instale o Google Drive Desktop em seu computador de trabalho.
2. Crie uma automação que salve todos os PDFs gerados na pasta sincronizada do Drive.
3. No seu computador local, você pode acessar e rodar o `streamlit run app.py`, ele irá ler as pastas locais usando a conexão de rede da sua máquina (Para acessar pelo celular na mesma rede de Wi-Fi: use o IP local exibido no terminal).

---

## 🔄 Rotina de Atualização Automática (Git)
Sempre que você alterar o código localmente (mudar uma cor, adicionar um botão, etc), basta rodar os **3 comandos mágicos** no seu Terminal do VS Code para que o painel Streamlit online atualize automaticamente em cerca de 1 minuto:

```bash
# 1. Preparar todas as mudanças
git add .

# 2. Empacotar com uma mensagem (ex: "ajustei as cores")
git commit -m "sua mensagem aqui"

# 3. Enviar para a nuvem
git push
```

## 🛠️ Extensão Futura
A estrutura foi construída utilizando arquitetura modular isolando regras de negócio em `services` e parsers em `parser`, o que permite escalabilidade para adicionar novos módulos ML ou integrações via API sem afetar o front-end Streamlit.
