import streamlit as st
from services.supabase_client import supabase

def sign_up(email, password, display_name):
    """Registra um novo usuário no Supabase e atualiza o display_name."""
    try:
        response = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {
                    "display_name": display_name
                }
            }
        })
        return response, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    """Realiza o login e retorna a sessão do Supabase."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response, None
    except Exception as e:
        return None, str(e)

def sign_out():
    """Desloga do Supabase e limpa a sessão local."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    if 'user' in st.session_state:
        del st.session_state['user']
    if 'session' in st.session_state:
        del st.session_state['session']
    st.rerun()

def update_profile_name(new_name):
    """Atualiza o nome da oficina no banco de dados e nos metadados."""
    user = get_current_user()
    if not user: return False
    
    try:
        # Atualiza o Auth (Identity)
        supabase.auth.update_user({"data": {"display_name": new_name}})
        
        # Atualiza a tabela pública
        supabase.table("profiles").update({"display_name": new_name}).eq("id", user.id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar perfil: {e}")
        return False

def get_current_user():
    """Retorna o usuário atual logado (se houver) a partir do session_state ou supabase."""
    if 'user' in st.session_state:
        return st.session_state['user']
        
    try:
        session = supabase.auth.get_session()
        if session:
            st.session_state['user'] = session.user
            st.session_state['session'] = session
            return session.user
    except Exception:
        pass
        
    return None
