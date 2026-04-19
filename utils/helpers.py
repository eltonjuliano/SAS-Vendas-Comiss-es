import plotly.express as px
import plotly.graph_objects as go

def format_currency(value):
    """Formats a float to Brazilian Real BRL"""
    if value == 0 or value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def plot_sales_evolution(df_grouped):
    """Line chart for total revenue over time"""
    fig = px.line(
        df_grouped, 
        x='date', 
        y='total_revenue', 
        title='Evolução de Vendas',
        markers=True,
        template='plotly_dark'
    )
    fig.update_layout(xaxis_title='Data', yaxis_title='Faturamento')
    return fig

def plot_commissions_evolution(df_grouped):
    """Line chart for commission over time"""
    fig = px.line(
        df_grouped, 
        x='date', 
        y='total_commission', 
        title='Evolução de Comissões',
        markers=True,
        template='plotly_dark'
    )
    fig.update_layout(xaxis_title='Data', yaxis_title='Comissão')
    return fig

def plot_category_comparison(total_tires, total_services_parts):
    """Bar chart comparing Tires vs Services+Parts"""
    fig = go.Figure(data=[
        go.Bar(name='Peças + Serviços (Sem Pneus)', x=['Categoria'], y=[total_services_parts], marker_color='#4C78A8'),
        go.Bar(name='Pneus', x=['Categoria'], y=[total_tires], marker_color='#F58518')
    ])
    fig.update_layout(
        title='Comparativo: Pneus vs Peças/Serviços',
        barmode='group',
        template='plotly_dark',
        yaxis_title='Valor (R$)'
    )
    return fig

def plot_time_analysis(df):
    """Bar chart for shop entry vs exit times"""
    if 'entrada_time' not in df.columns or 'saida_time' not in df.columns:
        return go.Figure()
        
    entries = df['entrada_time'].dropna().apply(lambda x: x.split(":")[0] + ":00" if isinstance(x, str) else None).value_counts().reset_index()
    entries.columns = ['Horário', 'Entradas']
    exits = df['saida_time'].dropna().apply(lambda x: x.split(":")[0] + ":00" if isinstance(x, str) else None).value_counts().reset_index()
    exits.columns = ['Horário', 'Saídas']
    
    # Merge and sort
    import pandas as pd
    merged = pd.merge(entries, exits, on='Horário', how='outer').fillna(0).sort_values('Horário')
    
    fig = go.Figure(data=[
        go.Bar(name='Entradas', x=merged['Horário'], y=merged['Entradas'], marker_color='#00CC96'),
        go.Bar(name='Saídas', x=merged['Horário'], y=merged['Saídas'], marker_color='#EF553B')
    ])
    fig.update_layout(
        title='Fluxo da Oficina (Entradas vs Saídas por Hora)',
        barmode='group',
        template='plotly_dark',
        xaxis_title='Horário',
        yaxis_title='Quantidade OS'
    )
    return fig

def plot_vehicle_frequency(df):
    """Horizontal bar chart for top vehicles"""
    if 'vehicle_model' not in df.columns:
        return go.Figure()
        
    counts = df['vehicle_model'].value_counts().head(10).reset_index()
    counts.columns = ['Veículo', 'Frequência']
    counts = counts.sort_values('Frequência', ascending=True)
    
    fig = px.bar(
        counts, 
        y='Veículo', 
        x='Frequência', 
        orientation='h',
        title='Top 10 Veículos mais Atendidos',
        template='plotly_dark',
        color='Frequência',
        color_continuous_scale='Blues'
    )
    return fig
