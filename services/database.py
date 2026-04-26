import streamlit as st
from services.supabase_client import supabase
from services.auth import get_current_user

def load_all_sales():
    """Carrega as OSs do usuário logado via Supabase."""
    user = get_current_user()
    if not user: return []
    
    try:
        # RLS will automatically filter if using anon key, but we pass user_id anyway if using service key.
        # Actually with anon key we just select all, RLS does the magic.
        response = supabase.table("os_records").select("*").eq("user_id", user.id).execute()
        
        # O supabase-py retorna response.data como uma lista de dicts.
        records = response.data
        
        # Ajustes de tipos para bater com o formato original do app.py
        for r in records:
            for key in ["total_parts", "total_services", "total_tires", "tire_quantity", "total_michelin", "michelin_quantity"]:
                if r.get(key) is None:
                    r[key] = 0.0 if "quantity" not in key else 0
                else:
                    r[key] = float(r[key]) if "quantity" not in key else int(float(r[key]))
                    
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
        # Busca OS existentes do usuário para evitar duplicidade
        existing_response = supabase.table("os_records").select("os_number").eq("user_id", user.id).execute()
        existing_os = set(str(row["os_number"]) for row in existing_response.data)
    except Exception:
        existing_os = set()
        
    rows_to_insert = []
    duplicates = []
    
    for item in parsed_data_list:
        os_num = str(item.get('os_number'))
        if os_num not in existing_os and os_num.strip() != "":
            # Prepara o registro
            row = item.copy()
            row["user_id"] = user.id
            
            # Limpeza rápida
            if 'date' in row and row['date']:
                row['date'] = str(row['date'])
            else:
                row['date'] = None
                
            rows_to_insert.append(row)
            existing_os.add(os_num)
        elif os_num in existing_os and os_num.strip() != "":
            if os_num not in duplicates:
                duplicates.append(os_num)
                
    if rows_to_insert:
        try:
            supabase.table("os_records").insert(rows_to_insert).execute()
        except Exception as e:
            st.error(f"Erro ao salvar OS: {e}")
            return 0, duplicates
            
    return len(rows_to_insert), duplicates

def delete_os(os_number):
    """Deleta uma OS do Supabase baseada no número."""
    user = get_current_user()
    if not user: return False
    
    try:
        response = supabase.table("os_records").delete().eq("os_number", str(os_number)).eq("user_id", user.id).execute()
        # No supabase-py v2, delete retorna os registros deletados em response.data
        if response.data:
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao remover a OS: {e}")
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
