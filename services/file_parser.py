import io
import mimetypes
import pandas as pd
from datetime import datetime
from parser.pdf_parser import extract_pdf_data

def detect_file_type(file_obj) -> str:
    """
    Detecta o tipo de arquivo baseado no nome e extensão.
    """
    name = getattr(file_obj, 'name', '').lower()
    if name.endswith('.pdf'):
        return 'pdf'
    elif name.endswith('.csv'):
        return 'csv'
    elif name.endswith('.xlsx') or name.endswith('.xls'):
        return 'excel'
    elif name.endswith('.docx'):
        return 'docx'
    elif name.endswith('.xml'):
        return 'xml'
    else:
        return 'unknown'

def parse_file(file_obj, profile_type: str) -> dict:
    """
    Extrai os dados do arquivo dependendo do tipo dele e do perfil comercial.
    Retorna:
    {
        'success': bool,
        'data': list of dicts (cada dict é uma venda),
        'message': str
    }
    """
    file_type = detect_file_type(file_obj)
    
    if file_type == 'pdf':
        if profile_type == 'Auto Center':
            # Usa o parser antigo especializado do Auto Center
            try:
                # O parser antigo retorna um dicionário único de uma OS
                data = extract_pdf_data(file_obj)
                # Precisamos converter isso para o formato de sales_records
                if not data.get('os_number'):
                    return {'success': False, 'data': [], 'message': 'Não foi possível encontrar o Número da OS no PDF.'}
                
                # Converte para o novo formato
                items = [
                    {'name': 'Peças', 'value': max(0.0, data.get('total_parts', 0.0) - data.get('total_tires', 0.0)), 'type': 'parts'},
                    {'name': 'Serviços', 'value': data.get('total_services', 0.0), 'type': 'services'},
                    {'name': 'Pneus', 'value': data.get('total_tires', 0.0), 'type': 'tires'}
                ]
                
                metadata = {k: v for k, v in data.items() if k not in ['os_number', 'date', 'customer', 'total_parts', 'total_services', 'total_tires']}
                
                sale_record = {
                    'identifier': data['os_number'],
                    'date': data.get('date'),
                    'client': data.get('customer', ''),
                    'total_value': data.get('total_parts', 0.0) + data.get('total_services', 0.0),
                    'items': items,
                    'metadata': metadata
                }
                
                return {'success': True, 'data': [sale_record], 'message': 'PDF processado com sucesso.'}
                
            except Exception as e:
                return {'success': False, 'data': [], 'message': f'Erro ao ler PDF: {str(e)}'}
        else:
            return {'success': False, 'data': [], 'message': f'Leitura de PDF não configurada para o perfil: {profile_type}. Utilize entrada manual.'}
            
    elif file_type == 'excel':
        try:
            df = pd.read_excel(file_obj)
            # Para planilhas, esperamos colunas padronizadas ou permitimos mapeamento no futuro.
            # No momento, implementamos um fallback genérico para planilhas.
            if 'Identificador' in df.columns and 'Valor Total' in df.columns:
                records = []
                for _, row in df.iterrows():
                    val = float(row['Valor Total']) if pd.notnull(row['Valor Total']) else 0.0
                    records.append({
                        'identifier': str(row['Identificador']),
                        'date': row.get('Data', datetime.now().date()),
                        'client': str(row.get('Cliente', '')),
                        'total_value': val,
                        'items': [{'name': 'Geral', 'value': val, 'type': 'general'}],
                        'metadata': {}
                    })
                return {'success': True, 'data': records, 'message': f'{len(records)} linhas lidas da planilha.'}
            else:
                return {'success': False, 'data': [], 'message': 'A planilha precisa das colunas "Identificador" e "Valor Total".'}
        except Exception as e:
            return {'success': False, 'data': [], 'message': f'Erro ao ler planilha: {str(e)}'}
            
    elif file_type == 'csv':
        try:
            df = pd.read_csv(file_obj)
            if 'Identificador' in df.columns and 'Valor Total' in df.columns:
                records = []
                for _, row in df.iterrows():
                    val = float(row['Valor Total']) if pd.notnull(row['Valor Total']) else 0.0
                    records.append({
                        'identifier': str(row['Identificador']),
                        'date': row.get('Data', datetime.now().date()),
                        'client': str(row.get('Cliente', '')),
                        'total_value': val,
                        'items': [{'name': 'Geral', 'value': val, 'type': 'general'}],
                        'metadata': {}
                    })
                return {'success': True, 'data': records, 'message': f'{len(records)} linhas lidas do CSV.'}
            else:
                return {'success': False, 'data': [], 'message': 'O CSV precisa das colunas "Identificador" e "Valor Total".'}
        except Exception as e:
            return {'success': False, 'data': [], 'message': f'Erro ao ler CSV: {str(e)}'}
            
    else:
        return {'success': False, 'data': [], 'message': f'Formato não suportado automaticamente ({file_type}).'}
