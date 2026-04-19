import streamlit as st
import pandas as pd
from datetime import datetime
from parser.pdf_parser import extract_pdf_data
from services.commission import process_sales_dataframe
from services.database import load_all_sales, save_new_sales
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
    /* Global size reduction for elegance */
    html, body, [class*="css"]  {
        font-size: 14px !important;
    }
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #4CAF50;
    }
    a.wa-btn {
        background-color: #25D366; 
        color: white; 
        padding: 5px 10px; 
        text-align: center; 
        text-decoration: none; 
        display: inline-block; 
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .crm-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: Arial, sans-serif;
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    .crm-table thead {
        background-color: #2b2b2b;
        color: white;
    }
    .crm-table th, .crm-table td {
        padding: 10px 12px;
        text-align: left;
        border-bottom: 1px solid #333;
    }
    .crm-table tbody tr:hover {
        background-color: #2a2a2a;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🚗 Dashboard Financeiro e Comissões")
    
    # ------------------------- SIDEBAR & DATABASE CARGA -------------------------
    st.sidebar.header("📁 Inserir Novos Relatórios")
    
    with st.sidebar.expander("Cadastrar PDFs", expanded=False):
        uploaded_files = st.file_uploader(
            "Faça upload dos PDFs (Ordem de Serviço)", 
            type="pdf", 
            accept_multiple_files=True
        )
        if st.button("Salvar no Banco", use_container_width=True) and uploaded_files:
            with st.spinner("Lendo PDFs e Vínculando ao Google Sheets..."):
                raw_data_list = []
                for file_obj in uploaded_files:
                    try:
                        data = extract_pdf_data(file_obj)
                        raw_data_list.append(data)
                    except Exception as e:
                        st.error(f"Erro ao processar {file_obj.name}: {e}")
                
                # Save to database
                inserted = save_new_sales(raw_data_list)
                if inserted > 0:
                    st.success(f"✅ {inserted} novas OS cadastradas com sucesso!")
                else:
                    st.warning("⚠️ Nenhuma nova OS encontrada (Pode ser que todas já estavam cadastradas).")
                
                # Refresh to fetch from db
                st.rerun()

    # Puxar TODOS os dados do Banco Histórico
    with st.spinner("Conectando ao Banco de Dados (Google Sheets)..."):
        db_raw_data = load_all_sales()
        
    if not db_raw_data:
        st.info("👈 Banco de dados vazio. Abra a guia lateral 'Cadastrar PDFs' e faça o upload das Ordens de Serviço para iniciar.")
        return

    # Calculate commissions and prepare dataframe from database records
    df = process_sales_dataframe(db_raw_data)
        
    if df.empty:
        st.warning("Nenhum dado válido para exibição.")
        return

    # Sidebar Filters
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
        
    # App is now divided in three tabs
    tab_geral, tab_clientes, tab_michelin = st.tabs(["📊 Visão Geral Administrativa", "👥 Área de Clientes (CRM)", "🛞 Bônus Michelin"])

    # ========================= TAB VISÃO GERAL =========================
    with tab_geral:
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

        st.dataframe(display_df, use_container_width=True, hide_index=True)


    # ========================= TAB ÁREA DE CLIENTES =========================
    with tab_clientes:
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
            
    # ========================= TAB BÔNUS MICHELIN =========================
    with tab_michelin:
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
            

if __name__ == "__main__":
    main()
