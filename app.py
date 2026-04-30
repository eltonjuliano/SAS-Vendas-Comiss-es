import streamlit as st
import pandas as pd
from datetime import datetime
from parser.pdf_parser import extract_pdf_data
from services.database import load_all_sales, save_new_sales, delete_os, load_finance_records, save_finance_record, delete_finance_record, update_finance_record
from services.auth import sign_up, sign_in, sign_out, get_current_user, update_profile_name, get_user_profile, update_cycle_dates
from services.file_parser import parse_file
from services.commission_engine import run_commission_engine
from models.commission_rules import CommissionRule
from services.supabase_client import supabase
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
    page_title="Comifyx",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for light theme, sleek fonts, and Mordomize-inspired UI
st.markdown("""
<style>
    /* Global size adjustments for better visualization */
    html, body, [class*="css"]  {
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
    h1 {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #1E2124 !important;
    }
    h2, h3 {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: #2D3748 !important;
    }
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #1E2124;
    }
    a.wa-btn {
        background-color: #25D366; 
        color: white; 
        padding: 8px 16px; 
        text-align: center; 
        text-decoration: none; 
        display: inline-block; 
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        transition: background-color 0.2s;
    }
    a.wa-btn:hover {
        background-color: #1EBE55;
    }
    .table-container {
        max-height: 400px;
        overflow-y: auto;
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: #FFFFFF;
        margin-bottom: 20px;
    }
    .table-container::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    .table-container::-webkit-scrollbar-thumb {
        background-color: #CBD5E0;
        border-radius: 4px;
    }
    .table-container::-webkit-scrollbar-corner {
        background-color: transparent;
    }
    .crm-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13.5px;
        font-family: 'Inter', sans-serif;
        background-color: #FFFFFF;
        color: #4A5568;
    }
    .crm-table thead th {
        position: sticky;
        top: 0;
        z-index: 1;
        background-color: #F8FAFC;
        color: #1A202C;
        font-weight: 600;
        border-bottom: 2px solid #E2E8F0;
        white-space: nowrap;
    }
    .crm-table th, .crm-table td {
        padding: 10px 12px;
        text-align: left;
        border-bottom: 1px solid #E2E8F0;
        white-space: nowrap;
    }
    .crm-table tbody tr:hover {
        background-color: #F1F5F9;
    }
    /* Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
    }

    /* Ocultar elementos nativos do Streamlit que parecem "sistema em teste" */
    [data-testid="stHeader"] {
        display: none !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* Ajustes da Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    /* Transformar Radio Buttons da Sidebar em Menu Moderno */
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none !important; /* Esconde a bolinha do radio */
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 12px 16px !important;
        margin-bottom: 4px !important;
        border-radius: 8px !important;
        border-left: 4px solid transparent !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: rgba(242, 92, 39, 0.05) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] p {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: #4A5568 !important;
    }
    
    /* Efeito de item Selecionado usando CSS :has() */
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: rgba(242, 92, 39, 0.1) !important;
        border-left: 4px solid #F25C27 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #F25C27 !important;
        font-weight: 700 !important;
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
    st.title("📈 Comifyx - Vendas e Comissões")
    
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

    # Sidebar Menu Navigation
    menu_options = ["⏱️ Dashboard", "👥 Clientes (CRM)", "💰 Receitas e Despesas", "📁 Importar Vendas", "📞 Suporte", "⚙️ Minha Conta"]
    
    _is_adm = is_admin()
    if _is_adm:
        menu_options.append("⚙️ Painel de Controle SaaS")
        
    selected_tab = st.sidebar.radio("", menu_options, label_visibility="collapsed")
    
    # Mensagens de alerta persistentes pós-reload
    if 'upload_success' in st.session_state:
        st.sidebar.success(f"✅ {st.session_state.pop('upload_success')} novas vendas cadastradas com sucesso!")
    if 'upload_duplicates' in st.session_state:
        dups = st.session_state.pop('upload_duplicates')
        st.sidebar.warning(f"⚠️ Atenção! As seguintes vendas JÁ EXISTIAM no sistema e foram ignoradas:\n{', '.join(dups)}")
    if 'upload_empty' in st.session_state:
        st.sidebar.warning("⚠️ Nenhuma venda foi importada.")
        del st.session_state['upload_empty']

    # Obter dados do perfil do usuário para regras
    user_profile = get_user_profile(user.id)
    profile_type = user_profile.get("profile_type", "Auto Center") if user_profile else "Auto Center"
    commission_rules_data = user_profile.get("commission_rules", []) if user_profile else []
    
    # Tour / Aviso para configurar regras se estiverem vazias
    if not commission_rules_data and selected_tab != "⚙️ Minha Conta":
        st.warning("👋 **Bem-vindo ao Comifyx!** Notamos que você ainda não configurou suas Regras de Comissão. Vá até a aba **⚙️ Minha Conta** para configurar como suas comissões devem ser calculadas.")

    # Puxar TODOS os dados do Banco Histórico
    with st.spinner("Conectando ao Banco de Dados..."):
        db_raw_data = load_all_sales()
        
    df = pd.DataFrame()
    if db_raw_data:
        # Se as comissões não vieram do banco (ou precisamos forçar recalculo dinamico):
        for rec in db_raw_data:
            if rec.get('total_commission', 0) == 0 and commission_rules_data:
                # Recalcula
                rec['total_commission'] = run_commission_engine(rec.get('items', []), commission_rules_data)
        
        df = pd.DataFrame(db_raw_data)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['year_month'] = df['date'].dt.to_period('M')

    # Trigger Dialogs based on action
    action_param = st.query_params.get("action")
    os_target = st.query_params.get("os")
    
    if action_param and os_target:
        # Clear the parameters from the URL immediately so it doesn't get stuck on F5
        st.query_params.clear()
        
        if action_param == "view":
            view_os_info(os_target, df)
        elif action_param == "delete":
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
    st.sidebar.markdown("**Filtros**")
    
    if not df.empty:
        df = df.dropna(subset=['date']) # Ensure we only filter valid dates
    min_date = df['date'].min().date() if not df.empty else datetime.now().date()
    max_date = df['date'].max().date() if not df.empty else datetime.now().date()

    # Puxar dados do ciclo
    user_profile = get_user_profile(user.id)
    
    from dateutil.relativedelta import relativedelta
    import calendar
    hoje = datetime.now().date()
    
    # Busca datas fixas se existirem, caso contrário define o mês atual
    primeiro_dia_mes = hoje.replace(day=1)
    ultimo_dia_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    
    custom_start_str = user_profile.get("cycle_start_date") if user_profile else None
    custom_end_str = user_profile.get("cycle_end_date") if user_profile else None
    
    try:
        if custom_start_str and custom_end_str:
            c_atual_start = pd.to_datetime(custom_start_str).date()
            c_atual_end = pd.to_datetime(custom_end_str).date()
        else:
            c_atual_start = primeiro_dia_mes
            c_atual_end = ultimo_dia_mes
    except:
        c_atual_start = primeiro_dia_mes
        c_atual_end = ultimo_dia_mes

    periodo_opcao = st.sidebar.selectbox("Período de Referência", [
        "Ciclo Definido no Perfil",
        "Personalizado"
    ])
    
    if periodo_opcao == "Ciclo Definido no Perfil":
        default_dates = (c_atual_start, c_atual_end)
    else:
        default_dates = (min_date, max_date)

    if periodo_opcao != "Personalizado":
        date_range = default_dates
        st.sidebar.info(f"Mostrando de {default_dates[0].strftime('%d/%m/%Y')} a {default_dates[1].strftime('%d/%m/%Y')}")
    else:
        date_range = st.sidebar.date_input(
            "Selecione as Datas Temporárias (Apenas Visualização)",
            value=(c_atual_start, c_atual_end)
        )
    
    # Filter DataFrame
    filtered_df = df.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        if not filtered_df.empty and 'date' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['date'] >= start_date) & 
                (filtered_df['date'] <= end_date)
            ]

    if filtered_df.empty and selected_tab in ["⏱️ Dashboard", "👥 Clientes (CRM)", "🏎️ Pneus (Michelin)", "💰 Receitas e Despesas"]:
        st.warning("Nenhum dado de vendas encontrado para os filtros selecionados.")
        # Não damos return aqui para permitir o acesso a Minha Conta e Suporte.
        
    # ========================= VISÃO GERAL =========================
    if selected_tab == "⏱️ Dashboard":
        if not filtered_df.empty:
            # KPI SECTION
            if 'total_revenue' not in filtered_df.columns:
                filtered_df['total_revenue'] = filtered_df.get('total_value', 0.0)
                
            total_sales = filtered_df['total_revenue'].sum()
            total_commission = filtered_df['total_commission'].sum()
    
            st.subheader("Visão Geral das Vendas")
            
            if profile_type == 'Auto Center':
                total_tires = filtered_df['total_tires'].sum()
                total_services_parts = total_sales - total_tires
                
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
                    <div class="metric-card" style="flex: 1; min-width: 200px;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px;">Faturamento Total</div>
                        <div class="metric-value">{format_currency(total_sales)}</div>
                        <div style="background-color: #E6FFFA; color: #38A169; display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-top: 8px;">↑ Faturamento</div>
                    </div>
                    <div class="metric-card" style="flex: 1; min-width: 200px;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px;">Peças e Serviços</div>
                        <div class="metric-value">{format_currency(total_services_parts)}</div>
                    </div>
                    <div class="metric-card" style="flex: 1; min-width: 200px;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px;">Vendas de Pneus</div>
                        <div class="metric-value">{format_currency(total_tires)}</div>
                    </div>
                    <div class="metric-card" style="flex: 1; min-width: 200px; border-left: 4px solid #F25C27;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px; font-weight: 600;">Sua Comissão</div>
                        <div class="metric-value" style="color: #F25C27;">{format_currency(total_commission)}</div>
                        <div style="background-color: #FFF3EB; color: #DD6B20; display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-top: 8px;">★ A Receber</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Perfil Genérico
                qtd_vendas = len(filtered_df)
                ticket_medio = total_sales / qtd_vendas if qtd_vendas > 0 else 0
                
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
                    <div class="metric-card" style="flex: 1; min-width: 200px;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px;">Volume de Vendas (R$)</div>
                        <div class="metric-value">{format_currency(total_sales)}</div>
                        <div style="background-color: #E6FFFA; color: #38A169; display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-top: 8px;">↑ Receita Global</div>
                    </div>
                    <div class="metric-card" style="flex: 1; min-width: 200px;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px;">Qtd. de Vendas</div>
                        <div class="metric-value">{qtd_vendas}</div>
                    </div>
                    <div class="metric-card" style="flex: 1; min-width: 200px;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px;">Ticket Médio</div>
                        <div class="metric-value">{format_currency(ticket_medio)}</div>
                    </div>
                    <div class="metric-card" style="flex: 1; min-width: 200px; border-left: 4px solid #F25C27;">
                        <div style="color: #718096; font-size: 0.9rem; margin-bottom: 5px; font-weight: 600;">Sua Comissão Estimada</div>
                        <div class="metric-value" style="color: #F25C27;">{format_currency(total_commission)}</div>
                        <div style="background-color: #FFF3EB; color: #DD6B20; display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-top: 8px;">★ A Receber</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
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
                if profile_type == 'Auto Center':
                    st.plotly_chart(plot_category_comparison(total_tires, total_services_parts), use_container_width=True)
                else:
                    st.info("Distribuição de vendas em breve.")
                
            # Row 2: Flow and Vehicles
            c3, c4 = st.columns(2)
            with c3:
                st.plotly_chart(plot_time_analysis(filtered_df), use_container_width=True)
            with c4:
                if profile_type == 'Auto Center':
                    st.plotly_chart(plot_vehicle_frequency(filtered_df), use_container_width=True)
                else:
                    st.info("Frequência de clientes em breve.")
    
            st.markdown("---")
    
            # FORECAST SECTION
            st.subheader("🔮 Previsão de Fechamento de Mês")
            if 'start_date' in locals() and 'end_date' in locals():
                forecast_result = generate_forecast(filtered_df, start_date, end_date) 
            else:
                forecast_result = None
            
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
                        label="Projeção Comissões", 
                        value=format_currency(forecast_result['projected_commission']), 
                        delta=format_currency(forecast_result['projected_commission'] - forecast_result['current_commission'])
                    )
        else:
            st.write("Volume de dados insuficiente para gerar previsão (mínimo de 2 dias no mês atual).")

        st.markdown("---")

        # TABLE SECTION (Anonymized)
        st.subheader("📋 Histórico de Vendas")
        
        if not filtered_df.empty:
            if profile_type == 'Auto Center':
                display_df = filtered_df[[
                    'os_number', 'date', 'vehicle_model', 'vehicle_year', 
                    'total_parts', 'total_services', 'total_tires', 'total_revenue'
                ]].copy()
                
                display_df['total_parts'] = display_df['total_parts'] - display_df['total_tires']
                for col in ['total_parts', 'total_services', 'total_tires', 'total_revenue']:
                    display_df[col] = display_df[col].apply(lambda x: format_currency(x))
                    
                display_df['date'] = display_df['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
                display_df.insert(0, 'Ações', display_df['os_number'].apply(
                    lambda os: f'<a href="/?action=view&os={os}" target="_self" style="text-decoration:none; font-size:16px; margin-right:12px;" title="Consultar OS">🔍</a>'
                               f'<a href="/?action=delete&os={os}" target="_self" style="text-decoration:none; font-size:16px;" title="Excluir OS">🗑️</a>'
                ))
                
                display_df.rename(columns={
                    'os_number': 'OS Nº', 'date': 'Data', 'vehicle_model': 'Modelo', 
                    'vehicle_year': 'Ano', 'total_parts': 'Peças (s/ pneu)', 
                    'total_services': 'Serviços', 'total_tires': 'Pneus', 'total_revenue': 'Total'
                }, inplace=True)
            else:
                display_df = filtered_df[[
                    'identifier', 'date', 'client', 'total_revenue', 'total_commission'
                ]].copy()
                
                for col in ['total_revenue', 'total_commission']:
                    display_df[col] = display_df[col].apply(lambda x: format_currency(x))
                    
                display_df['date'] = display_df['date'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else '')
                display_df.insert(0, 'Ações', display_df['identifier'].apply(
                    lambda os: f'<a href="/?action=delete&os={os}" target="_self" style="text-decoration:none; font-size:16px;" title="Excluir">🗑️</a>'
                ))
                
                display_df.rename(columns={
                    'identifier': 'Identificador', 'date': 'Data', 'client': 'Cliente', 
                    'total_revenue': 'Total da Venda', 'total_commission': 'Comissão Calculada'
                }, inplace=True)

            # Usar tabela HTML
            html_table = display_df.to_html(escape=False, index=False, classes="crm-table", border=0)
            wrapped_table = f'<div class="table-container">{html_table}</div>'
            st.write(wrapped_table, unsafe_allow_html=True)
        else:
            st.info("Nenhuma venda no período filtrado.")


    # ========================= CRM DE CLIENTES =========================
    elif selected_tab == "👥 Clientes (CRM)":
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
            st.write(f'<div class="table-container">{html_table}</div>', unsafe_allow_html=True)
            
    # ========================= BÔNUS MICHELIN =========================
    elif selected_tab == "🏎️ Pneus (Michelin)":
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
            

    # ========================= GESTÃO DE RECEBÍVEIS E DESPESAS =========================
    elif selected_tab == "💰 Receitas e Despesas":
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
                
                # Dividir df (mantendo apenas colunas relevantes)
                cols_to_keep = ['Ações', 'data', 'categoria', 'descricao', 'valor']
                cols_to_keep = [c for c in cols_to_keep if c in df_show.columns]
                
                df_gastos = df_show[df_show['tipo'] == 'Gasto'][cols_to_keep]
                df_receb = df_show[df_show['tipo'] == 'Recebível'][cols_to_keep]
                
                df_gastos.rename(columns={'data': 'Data', 'categoria': 'Categoria', 'descricao': 'Descrição', 'valor': 'Valor'}, inplace=True)
                df_receb.rename(columns={'data': 'Data', 'categoria': 'Categoria', 'descricao': 'Descrição', 'valor': 'Valor'}, inplace=True)
                
                col_g, col_r = st.columns(2)
                
                with col_g:
                    st.markdown("#### Despesas (Gastos)")
                    if not df_gastos.empty:
                        html_g = df_gastos.to_html(escape=False, index=False, classes="crm-table", border=0)
                        st.write(f'<div class="table-container">{html_g}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("Sem despesas no período.")
                        
                with col_r:
                    st.markdown("#### Receitas (Adicionais)")
                    if not df_receb.empty:
                        html_r = df_receb.to_html(escape=False, index=False, classes="crm-table", border=0)
                        st.write(f'<div class="table-container">{html_r}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("Sem receitas avulsas no período.")
            else:
                st.info("Nenhum lançamento no período filtrado.")
        else:
            st.info("Você ainda não possui lançamentos financeiros.")
            st.write(f"Sua previsão com base apenas em Vendas de OS nesse período: **{format_currency(total_commission)}**")

    # ========================= IMPORTAR VENDAS =========================
    elif selected_tab == "📁 Importar Vendas":
        st.subheader("📁 Importar Vendas")
        st.write("Faça upload de arquivos (PDF, CSV, Excel) ou insira manualmente suas vendas.")
        
        tab_upload, tab_manual = st.tabs(["📤 Upload de Arquivos", "✍️ Entrada Manual (Fallback)"])
        
        with tab_upload:
            uploaded_files = st.file_uploader(
                "Selecione um ou mais arquivos", 
                type=["pdf", "csv", "xlsx", "xls"], 
                accept_multiple_files=True
            )
            
            if st.button("Processar Arquivos", type="primary", use_container_width=True) and uploaded_files:
                with st.spinner("Lendo arquivos e extraindo dados..."):
                    raw_data_list = []
                    erros = []
                    
                    for file_obj in uploaded_files:
                        resultado = parse_file(file_obj, profile_type)
                        if resultado['success']:
                            raw_data_list.extend(resultado['data'])
                        else:
                            erros.append(f"{file_obj.name}: {resultado['message']}")
                    
                    if erros:
                        st.error("Alguns arquivos falharam na leitura. Você pode inserir os dados deles manualmente na aba ao lado.")
                        for erro in erros:
                            st.write(f"- {erro}")
                            
                    if raw_data_list:
                        inserted, duplicates = save_new_sales(raw_data_list)
                        if inserted > 0:
                            st.session_state['upload_success'] = inserted
                        if duplicates:
                            st.session_state['upload_duplicates'] = duplicates
                        
                        st.rerun()
                    elif not erros:
                        st.warning("Nenhum dado válido encontrado para importar.")
                        
        with tab_manual:
            st.write("Insira os dados da venda manualmente caso o upload automático falhe.")
            with st.form("manual_entry_form"):
                m_ident = st.text_input("Identificador da Venda (Ex: Número da OS, ID do Pedido)")
                m_data = st.date_input("Data da Venda")
                m_client = st.text_input("Cliente (Opcional)")
                m_valor = st.number_input("Valor Total (R$)", min_value=0.0, step=10.0, format="%.2f")
                
                # Se for auto center, tenta simular
                if profile_type == 'Auto Center':
                    st.write("Detalhamento (Opcional):")
                    c1, c2, c3 = st.columns(3)
                    with c1: m_parts = st.number_input("Peças (R$)", min_value=0.0, step=10.0)
                    with c2: m_serv = st.number_input("Serviços (R$)", min_value=0.0, step=10.0)
                    with c3: m_tires = st.number_input("Pneus (R$)", min_value=0.0, step=10.0)
                else:
                    m_parts = m_serv = m_tires = 0.0
                    
                if st.form_submit_button("Salvar Venda", type="primary"):
                    if m_ident and m_valor >= 0:
                        items = []
                        if profile_type == 'Auto Center' and (m_parts > 0 or m_serv > 0 or m_tires > 0):
                            items.append({'name': 'Peças', 'value': max(0.0, m_parts), 'type': 'parts'})
                            items.append({'name': 'Serviços', 'value': max(0.0, m_serv), 'type': 'services'})
                            items.append({'name': 'Pneus', 'value': max(0.0, m_tires), 'type': 'tires'})
                        else:
                            items.append({'name': 'Geral', 'value': m_valor, 'type': 'general'})
                            
                        record = [{
                            'identifier': m_ident,
                            'date': m_data,
                            'client': m_client,
                            'total_value': m_valor,
                            'items': items,
                            'metadata': {}
                        }]
                        ins, dup = save_new_sales(record)
                        if ins > 0:
                            st.success("Venda inserida com sucesso!")
                        elif dup:
                            st.error("Este Identificador já existe no sistema.")
                    else:
                        st.warning("Preencha o Identificador.")

    # ========================= SUPORTE (CLIENTE) =========================
    elif selected_tab == "📞 Suporte":
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
            novo_nome = st.text_input("Seu Nome Completo", value=user_nome_atual)
            if st.button("Salvar Alterações"):
                if update_profile_name(novo_nome):
                    st.success("Nome atualizado com sucesso!")
                    st.rerun()
                    
        st.markdown("---")
        with st.expander("🔄 Configurar Ciclo de Faturamento Fixo", expanded=True):
            st.write("Defina as **datas exatas** para o cálculo das suas comissões atuais. Estas datas ficarão salvas e serão o padrão do seu Dashboard até você alterá-las.")
            
            hoje = datetime.now().date()
            import calendar
            primeiro_dia_mes = hoje.replace(day=1)
            ultimo_dia_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
            
            custom_start_str = user_profile.get("cycle_start_date") if user_profile else None
            custom_end_str = user_profile.get("cycle_end_date") if user_profile else None
            
            try:
                if custom_start_str and custom_end_str:
                    c_start = pd.to_datetime(custom_start_str).date()
                    c_end = pd.to_datetime(custom_end_str).date()
                else:
                    c_start = primeiro_dia_mes
                    c_end = ultimo_dia_mes
            except:
                c_start = primeiro_dia_mes
                c_end = ultimo_dia_mes
            
            c1, c2 = st.columns(2)
            with c1:
                new_start = st.date_input("Data de Início", value=c_start)
            with c2:
                new_end = st.date_input("Data de Fechamento", value=c_end)
                
            if st.button("Salvar Período", type="primary", key="btn_salvar_periodo"):
                if update_cycle_dates(new_start, new_end):
                    st.success("Período fixo atualizado com sucesso! Atualizando tela...")
                    import time
                    time.sleep(1.5)
                    st.rerun()

        st.markdown("---")
        with st.expander("🏢 Perfil Comercial e Comissões", expanded=True):
            st.write("Adapte o sistema para o seu modelo de negócio e defina como você ganha comissão.")
            
            perfis_disponiveis = ["Auto Center", "Varejo", "Imóveis", "Veículos", "Consórcios", "Outro"]
            idx_perfil = perfis_disponiveis.index(profile_type) if profile_type in perfis_disponiveis else 0
            
            novo_perfil = st.selectbox("Seu Segmento de Atuação", perfis_disponiveis, index=idx_perfil)
            
            st.markdown("#### Tabela de Comissões")
            st.write("Adicione os produtos/serviços que você vende e a porcentagem de comissão correspondente para cada um.")
            
            regras_atuais = user_profile.get("commission_rules", []) if user_profile else []
            
            # Prepara dados para a tabela
            tabela_dados = []
            for r in regras_atuais:
                tabela_dados.append({
                    "Produto": r.get("item_type", ""),
                    "Comissão (%)": float(r.get("value", 0.0))
                })
                
            # Valores padrão se estiver vazio
            if not tabela_dados:
                if profile_type == 'Auto Center':
                    tabela_dados = [
                        {"Produto": "Peças", "Comissão (%)": 2.0},
                        {"Produto": "Serviços", "Comissão (%)": 2.0},
                        {"Produto": "Pneus", "Comissão (%)": 1.0}
                    ]
                else:
                    tabela_dados = [
                        {"Produto": "Geral", "Comissão (%)": 5.0},
                        {"Produto": "", "Comissão (%)": 0.0}
                    ]
            
            df_regras = pd.DataFrame(tabela_dados)
            
            edited_df = st.data_editor(
                df_regras,
                num_rows="dynamic",
                column_config={
                    "Produto": st.column_config.TextColumn(
                        "Produto ou Serviço (Ex: Pneus, Calça, etc)", 
                        required=True,
                        width="large"
                    ),
                    "Comissão (%)": st.column_config.NumberColumn(
                        "Comissão (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        format="%.1f %%",
                        width="medium"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("Salvar Perfil e Regras", type="primary"):
                try:
                    import uuid
                    novas_regras = []
                    for _, row in edited_df.iterrows():
                        prod = str(row["Produto"]).strip()
                        try:
                            val = float(row["Comissão (%)"])
                        except:
                            val = 0.0
                            
                        if prod: # Ignora linhas onde o produto ficou em branco
                            novas_regras.append({
                                "id": str(uuid.uuid4()),
                                "item_type": prod,
                                "rule_type": "percentage",
                                "value": val
                            })
                            
                    # Atualiza ou cria no Supabase
                    supabase.table("profiles").upsert({
                        "id": user.id,
                        "email": user.email,
                        "profile_type": novo_perfil,
                        "commission_rules": novas_regras
                    }).execute()
                    
                    st.success("Perfil e regras atualizados com sucesso!")
                    import time
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

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
    # Hide the default sidebar in the login page for a cleaner look
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    # Cria uma separação visual usando colunas com padding
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_text, col_space, col_form = st.columns([1.2, 0.2, 1])
    
    with col_text:
        st.markdown("""
        <div style='padding-top: 50px;'>
            <h1 style='font-size: 4rem; color: #F25C27; font-weight: 900; margin-bottom: 10px;'>Comifyx</h1>
            <h2 style='font-size: 2.2rem; color: #1E2124; font-weight: 700; line-height: 1.2;'>
                Plataforma inteligente para gestão de vendas, comissões e performance.
            </h2>
            <p style='font-size: 1.3rem; color: #4A5568; margin-top: 20px;'>
                Controle suas vendas. Escale seus resultados.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_form:
        st.markdown("""
        <div style='background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;'>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔒 Acesso Seguro", "👤 Criar Conta"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                email_login = st.text_input("E-mail corporativo ou pessoal")
                senha_login = st.text_input("Sua Senha", type="password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
                if submitted:
                    if email_login and senha_login:
                        with st.spinner("Autenticando..."):
                            res, err = sign_in(email_login, senha_login)
                            if err:
                                st.error(f"Erro ao entrar: Verifique suas credenciais.")
                            else:
                                st.success("Login efetuado com sucesso!")
                                st.rerun()
                    else:
                        st.warning("Preencha e-mail e senha.")
                    
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("signup_form"):
                nome_cad = st.text_input("Nome Completo")
                email_cad = st.text_input("E-mail Válido")
                senha_cad = st.text_input("Criar Senha (mín. 6 caracteres)", type="password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted_cad = st.form_submit_button("Finalizar Cadastro", type="primary", use_container_width=True)
                if submitted_cad:
                    if nome_cad and email_cad and len(senha_cad) >= 6:
                        with st.spinner("Criando sua conta..."):
                            res, err = sign_up(email_cad, senha_cad, nome_cad)
                            if err:
                                st.error(f"Erro no cadastro: Verifique os dados.")
                            else:
                                st.success("Conta criada! Você já pode fazer login na aba 'Acesso Seguro'.")
                    else:
                        st.warning("Preencha todos os campos. A senha deve ter no mínimo 6 caracteres.")
        
        st.markdown("</div>", unsafe_allow_html=True)

def landing_page():
    # Hide sidebar
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
            
            /* Landing Page Styles */
            .lp-logo { font-size: 1.8rem; font-weight: 900; color: #F25C27; padding-top: 10px; }
            .lp-hero { text-align: center; padding: 4rem 1rem 2rem 1rem; }
            .lp-hero h1 { font-size: 3.5rem !important; font-weight: 800; color: #1E2124; line-height: 1.2; max-width: 800px; margin: 0 auto; }
            .lp-hero h1 span { color: #F25C27; }
            .lp-hero p { font-size: 1.2rem; color: #4A5568; margin-top: 1.5rem; max-width: 600px; margin-left: auto; margin-right: auto; }
            .lp-cards { display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; margin-top: 3rem; }
            .lp-card { background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 2rem; width: 320px; text-align: left; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .lp-card h3 { color: #2D3748; font-size: 1.2rem; margin-bottom: 0.5rem; font-weight: 700; }
            .lp-card p { color: #718096; font-size: 0.95rem; line-height: 1.5; }
            .lp-card-icon { background: #FFF3EB; color: #F25C27; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 1rem; }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<div class='lp-logo'>Comifyx</div>", unsafe_allow_html=True)
    with c2:
        col_empty, col_btn = st.columns([3, 1])
        with col_btn:
            if st.button("Entrar", type="primary", use_container_width=True):
                st.session_state['show_login'] = True
                st.rerun()

    # Hero
    st.markdown("""
        <div class="lp-hero">
            <h1>Gerencie suas vendas e comissões de forma <span>simples e inteligente</span></h1>
            <p>Organize seus lançamentos, tenha previsibilidade de ganhos e assuma o controle total sobre sua performance comercial.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_btn_center1, col_btn_center2, col_btn_center3 = st.columns([1, 0.3, 1])
    with col_btn_center2:
        if st.button("Testar Agora", type="primary", use_container_width=True, key="hero_btn"):
            st.session_state['show_login'] = True
            st.rerun()

    # Features
    st.markdown("<h4 style='text-align: center; color: #F25C27; margin-top: 5rem; letter-spacing: 1.5px; font-weight: 700; font-size: 0.9rem;'>RECURSOS</h4>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1E2124; font-size: 2rem !important;'>Tudo o que você precisa para controlar seus resultados</h2>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="lp-cards">
            <div class="lp-card">
                <div class="lp-card-icon">📊</div>
                <h3>Dashboard Intuitivo</h3>
                <p>Visualize suas comissões em tempo real com gráficos e indicadores que mostram exatamente quanto você tem a receber.</p>
            </div>
            <div class="lp-card">
                <div class="lp-card-icon">💰</div>
                <h3>Controle de Receitas</h3>
                <p>Registre e categorize suas vendas e gastos de forma simples, separando entradas avulsas e despesas diárias.</p>
            </div>
            <div class="lp-card">
                <div class="lp-card-icon">🎯</div>
                <h3>Previsão e Metas</h3>
                <p>Acompanhe a projeção do fechamento do seu mês com Inteligência Artificial baseada no seu ritmo de vendas.</p>
            </div>
        </div>
        <br><br><br>
    """, unsafe_allow_html=True)

def main():
    user = get_current_user()
    if not user:
        if st.session_state.get('show_login', False):
            if st.button("← Voltar para o Site", key="back_btn"):
                st.session_state['show_login'] = False
                st.rerun()
            login_page()
        else:
            landing_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
