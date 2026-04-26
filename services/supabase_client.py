import os
import streamlit as st
from supabase import create_client, Client

# The URL and Key from Supabase Dashboard
SUPABASE_URL = "https://kedsovvypkuwmthsmhdj.supabase.co"
SUPABASE_KEY = "sb_publishable_BqWIbzBEkN9l_bCttG7JUg_VUrwXHux"

def init_connection() -> Client:
    """
    Inicializa e retorna o cliente do Supabase.
    """
    try:
        # Puxa dos secrets na produção, ou usa as chaves manuais localmente
        url = st.secrets.get("SUPABASE_URL", SUPABASE_URL)
        key = st.secrets.get("SUPABASE_KEY", SUPABASE_KEY)
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro ao inicializar o Supabase: {e}")
        return None

# Instância global do supabase
supabase = init_connection()
