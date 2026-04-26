import streamlit as st
import pandas as pd
from datetime import datetime
from parser.pdf_parser import extract_pdf_data
from services.commission import process_sales_dataframe
from services.database import load_all_sales, save_new_sales, delete_os, load_finance_records, save_finance_record, delete_finance_record, update_finance_record
from services.auth import sign_up, sign_in, sign_out, get_current_user, update_profile_name
from services.admin_db import is_admin, get_all_clients, update_subscription_status, create_support_ticket, get_my_tickets, get_all_tickets, answer_ticket, get_global_revenue, request_cancellation, reactivate_account, get_my_subscription
import uuid
from services.forecast import generate_forecast
from utils.helpers import (
    format_currency, 
    plot_sales_evolution, 
    plot_commissions_evolution, 
    plot_category_comparison,
    plot_time_analysis,
    plot_vehicle_frequency
)

# Configuration
st.set_page_config(
    page_title="Dashboard Automotivo",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme adjustments and sleek fonts
st.markdown("""
<style>
    /* Global size adjustments for better visualization */
    html, body, [class*="css"]  {
        font-size: 16px !important;
    }
    h1 {
        font-size: 32px !important;
    }
    h2, h3 {
        font-size: 24px !important;
    }
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    a.wa-btn {
        background-color: #25D366; 
        color: white; 
        padding: 6px 12px; 
        text-align: center; 
        text-decoration: none; 
        display: inline-block; 
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
    }
    .crm-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
        font-family: Arial, sans-serif;
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    .crm-table thead {
        background-color: #2b2b2b;
        color: white;
    }
    .crm-table th, .crm-table td {
        padding: 12px 14px;
        text-align: left;
        border-bottom: 1px solid #333;
    }
    .crm-table tbody tr:hover {
        background-color: #2a2a2a;
    }
</style>
""", unsafe_allow_html=True)

@st.dialog("Confirmar Exclusão de OS")
def confirm_delete_os(os_number):
    st.warning(f"Tem certeza que deseja excluir permanentemente a OS **{os_number}**?")
    if st.button("Sim, Excluir OS", type="primary", use_container_width=True):
        from services.database import delete_os
        if delete_os(os_number):
            st.success(f"OS {os_number} excluída da base de dados!")
        else:
            st.error("Erro ou OS não encontrada.")
        st.rerun()
    if st.button("Cancelar", use_container_width=True):
        st.rerun()

@st.dialog("Detalhes Completos da OS", width="large")
def view_os_info(os_number, df_completo):
    os_data = df_completo[df_completo['os_number'].astype(str) == str(os_number)]
    if os_data.empty:
        st.error("OS não encontrada nos relatórios.")
    else:
        row = os_data.iloc[0]
        st.markdown(f"## OS Selecionada: `{os_number}`")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"💼 **Cliente:** {row.get('customer', 'N/A')}")
            
            contato = str(row.get('contact', 'N/A'))
            if contato != 'N/A' and contato.strip() != "":
                import re
                clean_phone = re.sub(r'\D', '', contato)
                st.write(f"📞 **Contato:** [{contato}](https://wa.me/55{clean_phone})")
            else:
                st.write("📞 **Contato:** N/A")
                
            st.write(f"📧 **E-mail:** {row.get('email', 'N/A')}")
        with c2:
            st.write(f"📅 **Data:** {row['date'].strftime('%d/%m/%Y') if pd.notnull(row['date']) else 'N/A'}")
            st.write(f"🚘 **Veículo:** {row.get('vehicle_model', 'N/A')} ({row.get('vehicle_year', 'N/A')})")
            st.write(f"📌 **Placa:** {row.get('plate', 'N/A')}")
            
        st.markdown("---")
        st.markdown("### Valores Faturados")
        f1, f2, f3, f4 = st.columns(4)
        with f1: st.metric("Peças", format_currency(row.get('total_parts', 0)))
        with f2: st.metric("Serviços", format_currency(row.get('total_services', 0)))
        with f3: st.metric("Pneus", format_currency(row.get('total_tires', 0)))
        with f4: st.metric("Receita Total", format_currency(row.get('total_revenue', 0)))
        
        if row.get('total_michelin', 0) > 0:
            st.info(f"Michelin: **{row.get('michelin_quantity', 0)} pneus**. Volume de {format_currency(row.get('total_michelin', 0))}")
            
    if st.button("Fechar Informações", use_container_width=True):
        st.rerun()

@st.dialog("Editar Lançamento Financeiro")
def edit_finance_modal(record_id, df_fin):
    rec_data = df_fin[df_fin['id'].astype(str) == str(record_id)]
    if rec_data.empty:
        st.error("Registro financeiro não encontrado.")
    else:
        row = rec_data.iloc[0]
        st.markdown(f"**Modificando:** {row['categoria']} ({row['tipo']})")
        
        n_desc = st.text_input("Descrição", value=str(row.get('descricao', '')))
        
        val_atual = float(row.get('valor', 0.0))
        n_val = st.number_input("Valor (R$)", value=val_atual, min_value=0.0, step=10.0, format="%.2f")
        
        # Como row['data'] pode ser datetime ou string, formatamos p/ Date
        try:
            curr_date = pd.to_datetime(row['data']).date()
        except:
            from datetime import date
            curr_date = date.today()
            
        n_data = st.date_input("Data do Registro", value=curr_date)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar Alteração", type="primary", use_container_width=True):
                new_dict = {
                    "id": record_id,
                    "data": n_data.strftime("%Y-%m-%d"),
                    "tipo": row['tipo'],
                    "categoria": row['categoria'],
                    "descricao": n_desc,
                    "valor": n_val
                }
                if update_finance_record(new_dict):
                    st.success("Alterado com sucesso!")
                else:
                    st.error("Erro interno no salvamento.")
                st.query_params.clear()
                st.rerun()
        with c2:
            if st.button("Cancelar", use_container_width=True):
                st.query_params.clear()
                st.rerun()

def render_dashboard():
    st.title("🚗 Dashboard Financeiro e Comissões")
    
    # ------------------------- SIDEBAR & LOGOUT -------------------------
    user = get_current_user()
    nome_usuario = user.user_metadata.get('display_name', user.email) if user else 'Usuário'
    st.sidebar.markdown(f"**Olá, {nome_usuario}!**")
    if st.sidebar.button("🚪 Sair do Sistema"):
        sign_out()
    
    st.sidebar.markdown("---")
    
    # ------------------------- VERIFICA STATUS DA ASSINATURA -------------------------
    my_sub = get_my_subscription()
    sub_status = my_sub.get('status', 'Ativo') if my_sub else 'Ativo'
    
    # Se a conta estiver cancelada, bloqueia acesso e mostra apenas reativação
    if sub_status == 'Cancelado':
        st.error("🚫 Sua assinatura está cancelada.")
        st.write("Seu acesso ao sistema foi suspenso. Todos os seus dados, clientes e relatórios estão seguros conosco por **6 meses**.")
        st.write("Para voltar a usar o sistema e recuperar seu acesso imediatamente, reative sua conta.")
        if st.button("Reativar Minha Assinatura", type="primary"):
            reactivate_account()
            st.success("Conta reativada! Bem-vindo de volta.")
            st.rerun()
        return

    # ------------------------- SIDEBAR & DATABASE CARGA -------------------------
    st.sidebar.header("📁 Inserir Novos Relatórios")
    
    with st.sidebar.expander("Cadastrar PDFs", expanded=False):
        uploaded_files = st.file_uploader(
            "Faça upload dos PDFs (Ordem de Serviço)", 
            type="pdf", 
            accept_multiple_files=True
        )
        if st.button("Processar Ordens de Serviço", type="primary", use_container_width=True) and uploaded_files:
            with st.spinner("Lendo PDFs e calculando comissões..."):
                raw_data_list = []
                for file_obj in uploaded_files:
                    try:
                        data = extract_pdf_data(file_obj)
                        raw_data_list.append(data)
                    except Exception as e:
                        st.error(f"Erro ao processar {file_obj.name}: {e}")
                
                # Save to database
                inserted, duplicates = save_new_sales(raw_data_list)
                if inserted > 0:
                    st.session_state['upload_success'] = inserted
                
                if duplicates:
                    st.session_state['upload_duplicates'] = duplicates
                elif inserted == 0 and not duplicates:
                    st.session_state['upload_empty'] = True
                
                # Refresh to fetch from db
                st.rerun()
                
    # Mensagens de alerta persistentes pós-reload
    if 'upload_success' in st.session_state:
        st.sidebar.success(f"✅ {st.session_state.pop('upload_success')} novas OS cadastradas com sucesso!")
    if 'upload_duplicates' in st.session_state:
        dups = st.session_state.pop('upload_duplicates')
        st.sidebar.warning(f"⚠️ Atenção! As seguintes OS JÁ EXISTIAM no sistema e portanto foram ignoradas:\n{', '.join(dups)}")
    if 'upload_empty' in st.session_state:
        st.sidebar.warning("⚠️ Nenhuma OS foi lida.")
        del st.session_state['upload_empty']

    # Puxar TODOS os dados do Banco Histórico
    with st.spinner("Conectando ao Banco de Dados (Supabase)..."):
        db_raw_data = load_all_sales()
        
    if not db_raw_data:
        st.info("👈 Banco de dados vazio. Abra a guia lateral 'Cadastrar PDFs' e faça o upload das Ordens de Serviço para iniciar.")
        return

    # Calculate commissions and prepare dataframe from database records
    df = process_sales_dataframe(db_raw_data)
        
    if df.empty:
        st.warning("Nenhum dado válido para exibição.")
        return

    # Trigger Dialogs based on action
    action_param = st.query_params.get("action")
    os_target = st.query_params.get("os")
    
    if action_param and os_target:
        # Clear the parameters from the URL immediately so it doesn't get stuck on F5
        st.query_params.clear()
        
        if action_param == "delete":
            confirm_delete_os(os_target)
        elif action_param == "delfin":
            delete_finance_record(os_target)
            st.rerun()
        elif action_param == "editfin":
            try:
                # Carregado sob demanda na memória
                tmp_fin = load_finance_records()
                if tmp_fin:
                    df_tmp = pd.DataFrame(tmp_fin)
                    edit_finance_modal(os_target, df_tmp)
            except: pass

    # Sidebar Filters
    st.sidebar.markdown("---")
    st.sidebar.header("🧭 Menu de Navegação")
    menu_options = ["📊 Visão Geral Administrativa", "👥 Área de Clientes (CRM)", "🛞 Bônus Michelin", "💰 Gestão de Recebíveis", "📞 Suporte ao Cliente", "⚙️ Minha Conta"]
    
    _is_adm = is_admin()
    if _is_adm:
        menu_options.append("⚙️ Painel de Controle SaaS")
        
    selected_tab = st.sidebar.radio("Selecione a área", menu_options)
    
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros")
    df = df.dropna(subset=['date']) # Ensure we only filter valid dates
    min_date = df['date'].min()
    max_date = df['date'].max()

    date_range = st.sidebar.date_input(
        "Período de Venda",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Filter DataFrame
    filtered_df = df.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & 
            (filtered_df['date'] <= end_date)
        ]

    if filtered_df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return
        

    # ========================= VISÃO GERAL =========================
    if selected_tab == "📊 Visão Geral Administrativa":
        # KPI SECTION
        total_sales = filtered_df['total_revenue'].sum()
        total_tires = filtered_df['total_tires'].sum()
        total_services_parts = filtered_df['total_revenue'].sum() - total_tires
        total_commission = filtered_df['total_commission'].sum()

        st.subheader("📊 Indicadores Principais")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(label="Faturamento Total", value=format_currency(total_sales))
        with kpi2:
            st.metric(label="Total Peças/Serviços", value=format_currency(total_services_parts))
        with kpi3:
            st.metric(label="Total Pneus", value=format_currency(total_tires))
        with kpi4:
            st.metric(label="Comissão Total Estimada", value=format_currency(total_commission))

        st.markdown("---")

        # CHARTS SECTION
        st.subheader("📈 Análise Gráfica e Operacional")
        
        # Row 1: Sales / Commissions
        daily_sales = filtered_df.groupby('date').agg(
            total_revenue=('total_revenue', 'sum'),
            total_commission=('total_commission', 'sum')
        ).reset_index()

        c1, c2 = st.columns([2, 1])
        with c1:
            tb1, tb2 = st.tabs(["Evolução Faturamento", "Evolução Comissões"])
            with tb1:
                st.plotly_chart(plot_sales_evolution(daily_sales), use_container_width=True)
            with tb2:
                st.plotly_chart(plot_commissions_evolution(daily_sales), use_container_width=True)
        with c2:
            st.plotly_chart(plot_category_comparison(total_tires, total_services_parts), use_container_width=True)
            
        # Row 2: Flow and Vehicles
        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(plot_time_analysis(filtered_df), use_container_width=True)
        with c4:
            st.plotly_chart(plot_vehicle_frequency(filtered_df), use_container_width=True)

        st.markdown("---")

        # FORECAST SECTION
        st.subheader("🔮 Previsão de Fechamento de Mês")
        forecast_result = generate_forecast(df) 
        
        if forecast_result:
            fc1, fc2, fc3 = st.columns(3)
            month_label = forecast_result['month']
            
            with fc1:
                st.info(f"**Referência:** Mês {month_label}")
                st.write("Baseado no ritmo de vendas atual utilizando Regressão Linear.")
            with fc2:
                st.metric(
                    label="Projeção Faturamento", 
                    value=format_currency(forecast_result['projected_revenue']), 
                    delta=format_currency(forecast_result['projected_revenue'] - forecast_result['current_revenue'])
                )
            with fc3:
                st.metric(
                    label="Projeção Comissão", 
                    value=format_currency(forecast_result['projected_commission']),
                    delta=format_currency(forecast_result['projected_commission'] - forecast_result['current_commission'])
                )
        else:
            st.write("Volume de dados insuficiente para gerar previsão (mínimo de 2 dias no mês atual).")

        st.markdown("---")

        # TABLE SECTION (Anonymized)
        st.subheader("📋 Histórico Anonimizado de OS")
        
        # Determine explicit separated parts/services
        display_df = filtered_df[[
            'os_number', 'date', 'vehicle_model', 'vehicle_year', 
            'total_parts', 'total_services', 'total_tires', 'total_revenue'
        ]].copy()
        
        # Deduct tires from total_parts for the explicit display
        display_df['total_parts'] = display_df['total_parts'] - display_df['total_tires']
        
        # Format Currency
        for col in ['total_parts', 'total_services', 'total_tires', 'total_revenue']:
            display_df[col] = display_df[col].apply(lambda x: format_currency(x))
            
        # Ensure date format has no time
        display_df['date'] = display_df['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
        
        # Injetar links de ação em HTML (Os Ícones de Consultar e Excluir)
        display_df.insert(0, 'Ações', display_df['os_number'].apply(
            lambda os: f'<a href="/?action=view&os={os}" target="_self" style="text-decoration:none; font-size:16px; margin-right:12px;" title="Consultar OS">🔍</a>'
                       f'<a href="/?action=delete&os={os}" target="_self" style="text-decoration:none; font-size:16px;" title="Excluir OS">🗑️</a>'
        ))
        
        display_df.rename(columns={
            'os_number': 'OS Nº',
            'date': 'Data',
            'vehicle_model': 'Modelo',
            'vehicle_year': 'Ano',
            'total_parts': 'Peças (s/ pneu)',
            'total_services': 'Serviços',
            'total_tires': 'Pneus',
            'total_revenue': 'Total'
        }, inplace=True)

        # Usar tabela HTML para suportar ícones e links clicáveis de forma nativa e rápida
        html_table = display_df.to_html(escape=False, index=False, classes="crm-table", border=0)
        st.write(html_table, unsafe_allow_html=True)


    # ========================= ÁREA DE CLIENTES =========================
    elif selected_tab == "👥 Área de Clientes (CRM)":
        st.subheader("🔐 Acesso Restrito: Banco de Clientes")
        
        if "crm_authed" not in st.session_state:
            st.session_state["crm_authed"] = False
            
        if not st.session_state["crm_authed"]:
            pwd = st.text_input("Insira a senha de acesso ao CRM:", type="password")
            if st.button("Acessar"):
                if pwd == "y6b1r11!!":
                    st.session_state["crm_authed"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
        else:
            if st.button("Bloquear CRM"):
                st.session_state["crm_authed"] = False
                st.rerun()
                
            st.markdown("---")
            st.write("### 💼 Gestão de Pós-Venda e CRM")
            
            # Preparation of the CRM dataframe
            crm_df = filtered_df[[
                'os_number', 'date', 'customer', 'contact', 'email', 'plate', 'tire_quantity'
            ]].copy()
            
            # Check for Google Review Followup (1-3 days ago)
            hoje = datetime.now().date()
            
            # Helper to generate Whatsapp links
            # We strip non-numeric from contact
            import re
            
            def create_wa_link(phone, text):
                clean_phone = re.sub(r'\D', '', str(phone))
                if len(clean_phone) >= 10:
                    return f'<a class="wa-btn" href="https://wa.me/55{clean_phone}?text={text}" target="_blank">📲 Whatsapp</a>'
                return "Sem contato"

            # Post-Sales Google Review logic & Tire retention logic
            crm_data = []
            
            for _, row in crm_df.iterrows():
                row_date = row['date']
                pneus = row['tire_quantity']
                cliente = str(row['customer']).title()
                
                # Regras de Pneu
                bene = "Nenhum"
                if pneus >= 4:
                    bene = "4 Kits Geo/Bal a cada 3m"
                elif pneus >= 2:
                    bene = "1 Kit Geo/Bal daqui a 3m"
                    
                target_date = "N/A"
                if pneus >= 2:
                    # 90 days
                    td = row_date + pd.Timedelta(days=90)
                    target_date = td.strftime('%d/%m/%Y')
                
                # Google Review Warning
                days_diff = (hoje - row_date.date()).days
                google_alerta = "⏳ Aguardando"
                wtext = "Olá!"
                if days_diff >= 1 and days_diff <= 5: # recent purchase
                    google_alerta = "✅ Pedir Avaliação"
                    msg = f"Olá {cliente}! Aqui é da Cantele Automotiva. Como ficou o carro após o serviço no dia {row_date.strftime('%d/%m')}? Se gostou do nosso atendimento, poderia nos avaliar no Google? [LINK_DO_GOOGLE_AQUI]"
                    from urllib.parse import quote
                    wtext = quote(msg)
                
                # Action links
                acao_wa = create_wa_link(row['contact'], wtext)
                
                crm_data.append({
                    "OS": row['os_number'],
                    "Data": row_date.strftime('%d/%m/%Y'),
                    "Cliente": cliente,
                    "Telefone": row['contact'],
                    "E-mail": row['email'],
                    "Qtd Pneus": pneus,
                    "Benefício Pneu": bene,
                    "Retorno Recomendado": target_date,
                    "Status Pós-venda": google_alerta,
                    "Ação": acao_wa
                })
                
            crm_table = pd.DataFrame(crm_data)
            
            # Show Table with HTML safely to render buttons and styles
            html_table = crm_table.to_html(escape=False, index=False, classes="crm-table", border=0)
            st.write(html_table, unsafe_allow_html=True)
            
    # ========================= BÔNUS MICHELIN =========================
    elif selected_tab == "🛞 Bônus Michelin":
        st.subheader("🛞 Relatório de Vendas: MICHELIN")
        st.write("Acompanhe o faturamento exclusivo de pneus da marca Michelin para repasses de bônus.")
        
        # Filter only OSs that sold Michelin tires
        if 'total_michelin' in filtered_df.columns:
            michelin_df = filtered_df[filtered_df['total_michelin'] > 0].copy()
            
            # KPIs
            total_michelin_revenue = michelin_df['total_michelin'].sum()
            total_michelin_qty = michelin_df['michelin_quantity'].sum()
            
            mk_1, mk_2 = st.columns(2)
            with mk_1:
                st.metric("Total em R$ Michelin", format_currency(total_michelin_revenue))
            with mk_2:
                st.metric("Quant. Pneus Michelin Vendidos", int(total_michelin_qty))
                
            st.markdown("---")
            
            if not michelin_df.empty:
                st.write("### 📋 Histórico de OSs com Pneus Michelin")
                
                # Format view
                mich_display = michelin_df[['os_number', 'date', 'customer', 'michelin_quantity', 'total_michelin']].copy()
                mich_display['date'] = mich_display['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
                mich_display['total_michelin'] = mich_display['total_michelin'].apply(lambda x: format_currency(x))
                mich_display.rename(columns={
                    'os_number': 'OS Nº',
                    'date': 'Data',
                    'customer': 'Cliente',
                    'michelin_quantity': 'Qtd. Michelin',
                    'total_michelin': 'Faturamento Michelin'
                }, inplace=True)
                
                st.dataframe(mich_display, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma venda de Pneu Michelin encontrada no período filtrado.")
        else:
            st.info("Atualize o banco de dados enviando novos relatórios para visualizar os dados Michelin.")
            

    # ========================= GESTÃO DE RECEBÍVEIS =========================
    elif selected_tab == "💰 Gestão de Recebíveis":
        st.subheader("💰 Gestão de Recebíveis e Gastos")
        st.write("Controle seu fluxo de caixa pessoal: adicione seus recebimentos extras, salários e suas despesas diárias.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            with st.expander("➕ Adicionar Gasto", expanded=True):
                g_cat = st.selectbox("Categoria de Gasto", ["COMBUSTÍVEL", "ALIMENTAÇÃO", "ALUGUEL", "CADASTRA NOVO GASTO"])
                if g_cat == "CADASTRA NOVO GASTO":
                    g_cat = st.text_input("Escreva a nova categoria de gasto:")
                
                g_desc = st.text_input("Descrição do Gasto (Opcional)")
                g_val = st.number_input("Valor do Gasto (R$)", min_value=0.0, step=10.0, format="%.2f")
                g_data = st.date_input("Data do Gasto")
                
                if st.button("Lançar Gasto", type="primary"):
                    if g_cat and g_val > 0:
                        rec = {
                            "id": str(uuid.uuid4()), "data": g_data.strftime("%Y-%m-%d"), 
                            "tipo": "Gasto", "categoria": g_cat, "descricao": g_desc, "valor": g_val
                        }
                        if save_finance_record(rec):
                            st.success("Gasto lançado!")
                            st.rerun()
                        else: st.error("Erro ao salvar.")
                    else:
                        st.warning("Preencha categoria e valor maiores que zero.")

        with c2:
            with st.expander("➕ Adicionar Recebível", expanded=True):
                r_cat = st.selectbox("Categoria de Recebimento", ["BÔNUS", "AJUDA DE CUSTO", "SALÁRIO FIXO", "NOVO RECEBÍVEL"])
                if r_cat == "NOVO RECEBÍVEL":
                    r_cat = st.text_input("Escreva a nova categoria de recebível:")
                
                r_desc = st.text_input("Descrição do Recebimento (Opcional)")
                r_val = st.number_input("Valor do Recebimento (R$)", min_value=0.0, step=10.0, format="%.2f")
                r_data = st.date_input("Data do Recebimento")
                
                if st.button("Lançar Recebível", type="primary"):
                    if r_cat and r_val > 0:
                        rec = {
                            "id": str(uuid.uuid4()), "data": r_data.strftime("%Y-%m-%d"), 
                            "tipo": "Recebível", "categoria": r_cat, "descricao": r_desc, "valor": r_val
                        }
                        if save_finance_record(rec):
                            st.success("Recebível lançado!")
                            st.rerun()
                        else: st.error("Erro ao salvar.")
                    else:
                        st.warning("Preencha categoria e valor maiores que zero.")

        st.markdown("---")
        
        # Para contabilizar a comissão neste saldo
        total_commission = filtered_df['total_commission'].sum() if not filtered_df.empty else 0.0
        
        fin_records = load_finance_records()
        if fin_records:
            df_fin = pd.DataFrame(fin_records)
            df_fin['data'] = pd.to_datetime(df_fin['data'])
            
            # Filtro baseado na sidebar
            df_fin = df_fin[(df_fin['data'] >= pd.to_datetime(start_date)) & (df_fin['data'] <= pd.to_datetime(end_date))]
            
            total_gastos = df_fin[df_fin['tipo'] == 'Gasto']['valor'].sum()
            total_receb = df_fin[df_fin['tipo'] == 'Recebível']['valor'].sum()
            
            total_estimado = total_receb + total_commission
            saldo_projetado = total_estimado - total_gastos
            
            st.subheader("📈 Projeção Financeira do Período Selecionado")
            
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("Total de Comissões (OS)", format_currency(total_commission))
            with k2: st.metric("Recebimentos Fixos/Extras", format_currency(total_receb))
            with k3: st.metric("Total de Gastos", format_currency(total_gastos), delta=f"- {format_currency(total_gastos)}", delta_color="inverse")
            with k4: st.metric("Saldo Final Esperado", format_currency(saldo_projetado), delta=format_currency(saldo_projetado), delta_color="normal")
            
            st.markdown("### 📋 Histórico de Lançamentos Pessoais")
            if not df_fin.empty:
                df_show = df_fin.copy()
                
                # Funções de Ação HTML
                def act_btns(rid):
                    return f'<a href="/?action=editfin&os={rid}" target="_self" style="text-decoration:none; font-size:16px; margin-right:8px;" title="Editar">✏️</a><a href="/?action=delfin&os={rid}" target="_self" style="text-decoration:none; font-size:16px;" title="Excluir">🗑️</a>'
                
                df_show.insert(0, 'Ações', df_show['id'].apply(act_btns))
                df_show['data'] = df_show['data'].apply(lambda x: x.strftime('%d/%m/%Y'))
                df_show['valor'] = df_show['valor'].apply(lambda x: format_currency(x))
                
                # Dividir df
                df_gastos = df_show[df_show['tipo'] == 'Gasto'].drop(columns=['id', 'tipo'])
                df_receb = df_show[df_show['tipo'] == 'Recebível'].drop(columns=['id', 'tipo'])
                
                df_gastos.rename(columns={'data': 'Data', 'categoria': 'Categoria', 'descricao': 'Descrição', 'valor': 'Valor'}, inplace=True)
                df_receb.rename(columns={'data': 'Data', 'categoria': 'Categoria', 'descricao': 'Descrição', 'valor': 'Valor'}, inplace=True)
                
                col_g, col_r = st.columns(2)
                
                with col_g:
                    st.markdown("#### Despesas (Gastos)")
                    if not df_gastos.empty:
                        html_g = df_gastos.to_html(escape=False, index=False, classes="crm-table", border=0)
                        st.write(html_g, unsafe_allow_html=True)
                    else:
                        st.caption("Sem despesas no período.")
                        
                with col_r:
                    st.markdown("#### Receitas (Adicionais)")
                    if not df_receb.empty:
                        html_r = df_receb.to_html(escape=False, index=False, classes="crm-table", border=0)
                        st.write(html_r, unsafe_allow_html=True)
                    else:
                        st.caption("Sem receitas avulsas no período.")
            else:
                st.info("Nenhum lançamento no período filtrado.")
        else:
            st.info("Você ainda não possui lançamentos financeiros.")
            st.write(f"Sua previsão com base apenas em Vendas de OS nesse período: **{format_currency(total_commission)}**")

    # ========================= SUPORTE (CLIENTE) =========================
    elif selected_tab == "📞 Suporte ao Cliente":
        st.subheader("📞 Central de Ajuda e Suporte")
        st.write("Teve algum problema ou tem uma dúvida? Abra um chamado abaixo e nossa equipe responderá em breve.")
        
        with st.expander("➕ Abrir Novo Chamado de Suporte", expanded=True):
            s_assunto = st.text_input("Assunto")
            s_msg = st.text_area("Descreva seu problema/dúvida detalhadamente")
            if st.button("Enviar Mensagem", type="primary"):
                if s_assunto and s_msg:
                    if create_support_ticket(s_assunto, s_msg):
                        st.success("Chamado enviado com sucesso! Aguarde nosso retorno.")
                        st.rerun()
                else:
                    st.warning("Preencha o assunto e a mensagem.")
        
        st.markdown("---")
        st.markdown("### 📋 Meus Chamados")
        tickets = get_my_tickets()
        if tickets:
            for t in tickets:
                status_icon = "🟢 Aberto" if t.get('status') == 'Aberto' else "🔴 Fechado"
                with st.expander(f"[{status_icon}] {t.get('subject')} - {t.get('created_at')[:10]}"):
                    st.write("**Sua mensagem:**")
                    st.info(t.get('message'))
                    st.write("**Resposta da Equipe:**")
                    if t.get('admin_reply'):
                        st.success(t.get('admin_reply'))
                    else:
                        st.caption("Aguardando resposta...")
        else:
            st.info("Você não tem chamados de suporte em aberto.")

    # ========================= MINHA CONTA (CLIENTE) =========================
    elif selected_tab == "⚙️ Minha Conta":
        st.subheader("⚙️ Configurações da Conta")
        
        with st.expander("👤 Alterar Nome do Perfil", expanded=True):
            user_nome_atual = user.user_metadata.get('display_name', '')
            novo_nome = st.text_input("Nome da Oficina / Seu Nome", value=user_nome_atual)
            if st.button("Salvar Alterações"):
                if update_profile_name(novo_nome):
                    st.success("Nome atualizado com sucesso!")
                    st.rerun()
                    
        st.markdown("---")
        st.subheader("Plano e Assinatura")
        
        my_sub = get_my_subscription()
        if my_sub:
            if my_sub.get('cancel_at_period_end'):
                st.warning("⚠️ Você solicitou o cancelamento da sua assinatura.")
                st.write("Sua conta continuará ativa até o dia do vencimento da sua próxima fatura. Após essa data, o acesso será bloqueado e seus dados mantidos por 6 meses.")
                if st.button("Desfazer Cancelamento (Reativar)"):
                    reactivate_account()
                    st.success("Cancelamento anulado!")
                    st.rerun()
            else:
                st.info("Sua assinatura está **Ativa**.")
                with st.expander("⚠️ Cancelar Assinatura"):
                    st.write("Tem certeza que deseja cancelar sua assinatura?")
                    st.write("Ao cancelar, você terá acesso ao sistema até a data do seu próximo vencimento. Seus dados ficarão salvos por **6 meses** caso você decida voltar.")
                    
                    motivo = st.selectbox("Qual o motivo principal do cancelamento?", [
                        "Selecione um motivo",
                        "O valor está alto no momento",
                        "O sistema não funciona como eu gostaria",
                        "Outro motivo (Especifique abaixo)"
                    ])
                    
                    if motivo == "Outro motivo (Especifique abaixo)":
                        motivo_detalhe = st.text_area("Descreva o motivo:")
                        motivo_final = f"Outro: {motivo_detalhe}" if motivo_detalhe else ""
                    else:
                        motivo_final = motivo
                        
                    if st.button("Confirmar Cancelamento", type="primary"):
                        if motivo == "Selecione um motivo":
                            st.error("Por favor, selecione o motivo do cancelamento.")
                        elif motivo_final:
                            request_cancellation(motivo_final)
                            st.success("Sua solicitação foi registrada. Um alerta foi enviado à nossa equipe.")
                            st.rerun()

    # ========================= PAINEL DE CONTROLE (SaaS ADMIN) =========================
    elif selected_tab == "⚙️ Painel de Controle SaaS":
        st.subheader("⚙️ Painel de Administração do SaaS")
        st.write("Acesso exclusivo do Proprietário do Sistema.")
        
        tab_admin1, tab_admin2, tab_admin3 = st.tabs(["👥 Clientes e Mensalidades", "📞 Caixa de Entrada (Suporte)", "💰 Faturamento Global"])
        
        with tab_admin1:
            st.markdown("### Gestão de Clientes")
            clientes = get_all_clients()
            if clientes:
                for c in clientes:
                    c_id = c.get('id')
                    c_name = c.get('display_name') or 'Sem Nome'
                    c_email = c.get('email')
                    
                    subs = c.get('subscriptions')
                    if subs and isinstance(subs, list) and len(subs) > 0:
                        sub_status = subs[0].get('status', 'Sem Plano')
                    elif subs and isinstance(subs, dict):
                        sub_status = subs.get('status', 'Sem Plano')
                    else:
                        sub_status = 'Sem Plano'
                        
                    with st.expander(f"🏢 {c_name} | ✉️ {c_email} | Status: {sub_status.upper()}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            novo_status = st.selectbox("Status do Pagamento", ["Ativo", "Atrasado", "Cancelado"], index=["Ativo", "Atrasado", "Cancelado"].index(sub_status) if sub_status in ["Ativo", "Atrasado", "Cancelado"] else 0, key=f"status_{c_id}")
                            if st.button("Atualizar Status", key=f"btn_{c_id}"):
                                if update_subscription_status(c_id, novo_status):
                                    st.success("Atualizado!")
                                    st.rerun()
                        with c2:
                            st.write(f"**ID no Banco:** `{c_id}`")
                            st.write(f"**Cadastro em:** `{c.get('created_at')[:10]}`")
                            if subs and isinstance(subs, list) and len(subs) > 0:
                                sub_data = subs[0]
                                if sub_data.get('cancel_at_period_end'):
                                    st.error("🚨 SOLICITOU CANCELAMENTO")
                                    st.write(f"**Motivo:** {sub_data.get('cancellation_reason')}")
                            elif subs and isinstance(subs, dict):
                                if subs.get('cancel_at_period_end'):
                                    st.error("🚨 SOLICITOU CANCELAMENTO")
                                    st.write(f"**Motivo:** {subs.get('cancellation_reason')}")
            else:
                st.info("Nenhum cliente cadastrado ainda.")
                
        with tab_admin2:
            st.markdown("### Caixa de Entrada (Mensagens de Clientes)")
            all_tickets = get_all_tickets()
            if all_tickets:
                for t in all_tickets:
                    t_id = t.get('id')
                    t_status = t.get('status')
                    t_subject = t.get('subject')
                    t_msg = t.get('message')
                    prof = t.get('profiles') or {}
                    c_name = prof.get('display_name', 'Cliente Oculto')
                    
                    icon = "🟢 Aberto" if t_status == 'Aberto' else "🔴 Fechado"
                    with st.expander(f"[{icon}] De: {c_name} - {t_subject}"):
                        st.write(f"**Mensagem do cliente:**")
                        st.info(t_msg)
                        
                        if t_status == 'Aberto':
                            resposta = st.text_area("Escreva sua resposta para o cliente:", key=f"reply_{t_id}")
                            if st.button("Enviar Resposta e Fechar Chamado", key=f"btn_reply_{t_id}"):
                                if answer_ticket(t_id, resposta):
                                    st.success("Respondido!")
                                    st.rerun()
                        else:
                            st.write("**Sua resposta:**")
                            st.success(t.get('admin_reply'))
            else:
                st.info("Nenhum chamado no sistema.")
                
        with tab_admin3:
            st.markdown("### Visão Global de Receita")
            rev = get_global_revenue()
            if rev:
                r1, r2, r3 = st.columns(3)
                with r1:
                    st.metric("Clientes Ativos (Pagantes)", rev['active_clients'])
                with r2:
                    st.metric("MRR (Receita Mensal Recorrente)", format_currency(rev['mrr']))
                with r3:
                    st.metric("Total de OS Geradas na Plataforma", rev['total_os'])
                st.caption("Nota: MRR calculado baseado em valor fixo estimado. O valor real virá do Gateway de Pagamento futuramente.")
            else:
                st.write("Dados indisponíveis.")

def login_page():
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='font-size: 3rem; color: #4CAF50;'>Dashboard SaaS</h1>
        <p style='font-size: 1.2rem; color: #bbb;'>Gestão automotiva inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
        
        with tab1:
            st.subheader("Login Seguro")
            email_login = st.text_input("E-mail", key="login_email")
            senha_login = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", type="primary", use_container_width=True):
                if email_login and senha_login:
                    with st.spinner("Autenticando..."):
                        res, err = sign_in(email_login, senha_login)
                        if err:
                            st.error(f"Erro ao entrar: {err}")
                        else:
                            st.success("Login efetuado com sucesso!")
                            st.rerun()
                else:
                    st.warning("Preencha e-mail e senha.")
                    
            st.markdown("<br><center><p>Ou acesse com</p></center>", unsafe_allow_html=True)
            st.button("🔑 Entrar com o Google (Em breve)", use_container_width=True, disabled=True)
            
        with tab2:
            st.subheader("Nova Conta")
            nome_cad = st.text_input("Seu Nome/Oficina", key="cad_nome")
            email_cad = st.text_input("E-mail", key="cad_email")
            senha_cad = st.text_input("Senha (mín. 6 caracteres)", type="password", key="cad_pass")
            
            if st.button("Cadastrar", type="primary", use_container_width=True):
                if nome_cad and email_cad and len(senha_cad) >= 6:
                    with st.spinner("Criando sua conta..."):
                        res, err = sign_up(email_cad, senha_cad, nome_cad)
                        if err:
                            st.error(f"Erro no cadastro: {err}")
                        else:
                            st.success("Conta criada! Você já pode fazer login na aba 'Entrar'.")
                            st.info("Caso o Supabase exija confirmação, verifique a caixa de entrada do seu e-mail.")
                else:
                    st.warning("Preencha todos os campos. Senha deve ter no mínimo 6 caracteres.")

def main():
    user = get_current_user()
    if not user:
        login_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
