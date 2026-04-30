import streamlit as st
from services.supabase_client import supabase
from services.auth import get_current_user

def load_all_sales():
    """Carrega as OSs do usuário logado via Supabase."""
    user = get_current_user()
    if not user: return []
    
    try:
        response = supabase.table("sales_records").select("*").eq("user_id", user.id).execute()
        records = response.data
        
        for r in records:
            r['total_value'] = float(r.get('total_value', 0.0))
            r['total_commission'] = float(r.get('total_commission', 0.0))
            
            # Compatibility layer for legacy "Auto Center" app logic
            if r.get('metadata'):
                meta = r['metadata']
                r['os_number'] = r.get('identifier')
                r['customer'] = r.get('client')
                for key in ["tire_quantity", "total_michelin", "michelin_quantity"]:
                    if meta.get(key) is None:
                        r[key] = 0.0 if "quantity" not in key else 0
                    else:
                        r[key] = float(meta[key]) if "quantity" not in key else int(float(meta[key]))
                
                # Copy some other useful metadata up
                r['vehicle_model'] = meta.get('vehicle_model', '')
                r['vehicle_year'] = meta.get('vehicle_year', '')
                r['plate'] = meta.get('plate', '')
                r['contact'] = meta.get('contact', '')
                r['email'] = meta.get('email', '')
            
            # Extract items to specific columns if they exist (for Auto Center compatibility)
            r['total_parts'] = 0.0
            r['total_services'] = 0.0
            r['total_tires'] = 0.0
            
            if r.get('items'):
                for item in r['items']:
                    val = float(item.get('value', 0.0))
                    itype = item.get('type', '')
                    if itype == 'parts': r['total_parts'] += val
                    elif itype == 'services': r['total_services'] += val
                    elif itype == 'tires': r['total_tires'] += val
                    
        return records
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def save_new_sales(parsed_data_list):
    """
    Salva uma lista de dicionários de OS no Supabase.
    Retorna (inserted_count, list_of_duplicates).
    """
    user = get_current_user()
    if not user or not parsed_data_list: return 0, []
    
    try:
        # Busca vendas existentes do usuário para evitar duplicidade
        existing_response = supabase.table("sales_records").select("identifier").eq("user_id", user.id).execute()
        existing_ids = set(str(row["identifier"]) for row in existing_response.data)
    except Exception:
        existing_ids = set()
        
    rows_to_insert = []
    duplicates = []
    
    for item in parsed_data_list:
        ident = str(item.get('identifier'))
        if ident not in existing_ids and ident.strip() != "":
            # Prepara o registro
            row = item.copy()
            row["user_id"] = user.id
            
            # Limpeza rápida
            if 'date' in row and row['date']:
                row['date'] = str(row['date'])
            else:
                row['date'] = None
                
            rows_to_insert.append(row)
            existing_ids.add(ident)
        elif ident in existing_ids and ident.strip() != "":
            if ident not in duplicates:
                duplicates.append(ident)
                
    if rows_to_insert:
        try:
            supabase.table("sales_records").insert(rows_to_insert).execute()
        except Exception as e:
            st.error(f"Erro ao salvar Vendas: {e}")
            return 0, duplicates
            
    return len(rows_to_insert), duplicates

def delete_os(os_number):
    """Deleta uma venda do Supabase baseada no identificador."""
    user = get_current_user()
    if not user: return False
    
    try:
        response = supabase.table("sales_records").delete().eq("identifier", str(os_number)).eq("user_id", user.id).execute()
        # No supabase-py v2, delete retorna os registros deletados em response.data
        if response.data:
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao remover o registro: {e}")
        return False

# ======================== FINANCIAL MANAGEMENT ========================

def load_finance_records():
    """Retorna os lançamentos financeiros do usuário."""
    user = get_current_user()
    if not user: return []
    
    try:
        response = supabase.table("finance_records").select("*").eq("user_id", user.id).execute()
        records = response.data
        for r in records:
            r["valor"] = float(r.get("valor", 0.0))
        return records
    except Exception as e:
        st.error(f"Erro ao carregar fluxo financeiro: {e}")
        return []

def save_finance_record(record_dict):
    """Insere um novo registro financeiro no Supabase."""
    user = get_current_user()
    if not user: return False
    
    record_dict["user_id"] = user.id
    try:
        supabase.table("finance_records").insert(record_dict).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar finança: {e}")
        return False

def delete_finance_record(record_id):
    """Deleta um registro financeiro com base no ID."""
    user = get_current_user()
    if not user: return False
    
    try:
        response = supabase.table("finance_records").delete().eq("id", str(record_id)).eq("user_id", user.id).execute()
        if response.data:
            return True
        return False
    except Exception:
        return False

def update_finance_record(record_dict):
    """Atualiza um registro financeiro."""
    user = get_current_user()
    if not user: return False
    
    record_id = str(record_dict.get("id"))
    update_data = record_dict.copy()
    update_data.pop("id", None) # Não atualizamos o ID
    
    try:
        response = supabase.table("finance_records").update(update_data).eq("id", record_id).eq("user_id", user.id).execute()
        if response.data:
            return True
        return False
    except Exception as e:
        st.error(f"Erro na atualização: {e}")
        return False
