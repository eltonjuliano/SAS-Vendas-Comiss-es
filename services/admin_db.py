import streamlit as st
from services.supabase_client import supabase
from services.auth import get_current_user
from datetime import datetime

# ==========================================
# FUNÇÕES DE VERIFICAÇÃO DE ADMIN
# ==========================================
def is_admin():
    """Verifica se o usuário logado tem a role de 'admin' na tabela profiles."""
    user = get_current_user()
    if not user: return False
    
    try:
        response = supabase.table("profiles").select("role").eq("id", user.id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("role") == "admin"
        return False
    except Exception:
        return False

# ==========================================
# GESTÃO DE USUÁRIOS E ASSINATURAS (ADMIN)
# ==========================================
def get_all_clients():
    """Retorna todos os perfis de clientes com suas assinaturas (Apenas Admin)."""
    if not is_admin(): return []
    try:
        # Busca perfis
        resp_prof = supabase.table("profiles").select("id, email, display_name, created_at").eq("role", "client").execute()
        profiles = resp_prof.data
        
        # Busca assinaturas
        resp_subs = supabase.table("subscriptions").select("user_id, status, plan_name, next_billing_date").execute()
        subs_dict = {sub["user_id"]: sub for sub in resp_subs.data}
        
        # Faz o merge no Python
        for p in profiles:
            user_id = p["id"]
            if user_id in subs_dict:
                p["subscriptions"] = [subs_dict[user_id]]
            else:
                p["subscriptions"] = []
                
        return profiles
    except Exception as e:
        st.error(f"Erro ao buscar clientes: {e}")
        return []

def update_subscription_status(user_id, new_status):
    """Atualiza o status da assinatura (Ativo, Atrasado, Cancelado)."""
    if not is_admin(): return False
    try:
        supabase.table("subscriptions").update({"status": new_status, "updated_at": datetime.now().isoformat()}).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False

def request_cancellation(reason):
    """Solicita cancelamento pelo cliente."""
    user = get_current_user()
    if not user: return False
    try:
        supabase.table("subscriptions").update({
            "cancel_at_period_end": True, 
            "cancellation_reason": reason,
            "updated_at": datetime.now().isoformat()
        }).eq("user_id", user.id).execute()
        return True
    except Exception:
        return False

def reactivate_account():
    """Desfaz o pedido de cancelamento antes do bloqueio final."""
    user = get_current_user()
    if not user: return False
    try:
        supabase.table("subscriptions").update({
            "cancel_at_period_end": False,
            "cancellation_reason": None,
            "status": "Ativo",
            "updated_at": datetime.now().isoformat()
        }).eq("user_id", user.id).execute()
        return True
    except Exception:
        return False

def get_my_subscription():
    """Retorna a assinatura do usuário logado."""
    user = get_current_user()
    if not user: return None
    try:
        resp = supabase.table("subscriptions").select("*").eq("user_id", user.id).execute()
        if resp.data: return resp.data[0]
        return None
    except Exception:
        return None


# ==========================================
# SUPORTE (INBOX)
# ==========================================
def create_support_ticket(subject, message):
    """Cria um novo chamado de suporte (Visão do Cliente)."""
    user = get_current_user()
    if not user: return False
    try:
        supabase.table("support_tickets").insert({
            "user_id": user.id,
            "subject": subject,
            "message": message,
            "status": "Aberto"
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao criar chamado: {e}")
        return False

def get_my_tickets():
    """Retorna os chamados abertos pelo próprio cliente."""
    user = get_current_user()
    if not user: return []
    try:
        response = supabase.table("support_tickets").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        return response.data
    except Exception:
        return []

def get_all_tickets(status_filter=None):
    """Retorna todos os chamados de suporte do sistema, com os dados do cliente (Visão Admin)."""
    if not is_admin(): return []
    try:
        # Busca tickets
        query = supabase.table("support_tickets").select("*")
        if status_filter:
            query = query.eq("status", status_filter)
        resp_tickets = query.order("created_at", desc=True).execute()
        tickets = resp_tickets.data
        
        # Busca perfis para cruzar os nomes
        resp_prof = supabase.table("profiles").select("id, display_name, email").execute()
        prof_dict = {p["id"]: {"display_name": p["display_name"], "email": p["email"]} for p in resp_prof.data}
        
        # Faz o merge
        for t in tickets:
            user_id = t["user_id"]
            t["profiles"] = prof_dict.get(user_id, {"display_name": "Desconhecido", "email": ""})
            
        return tickets
    except Exception as e:
        st.error(f"Erro ao buscar chamados: {e}")
        return []

def answer_ticket(ticket_id, reply_text):
    """Responde a um chamado de suporte e o marca como fechado (Apenas Admin)."""
    if not is_admin(): return False
    try:
        supabase.table("support_tickets").update({
            "admin_reply": reply_text,
            "status": "Fechado",
            "replied_at": datetime.now().isoformat()
        }).eq("id", ticket_id).execute()
        return True
    except Exception:
        return False

# ==========================================
# DASHBOARD FINANCEIRO GLOBAL (ADMIN)
# ==========================================
def get_global_revenue():
    """Calcula o faturamento total e número de oficinas (Visão Admin)."""
    if not is_admin(): return None
    try:
        # Puxa quantas assinaturas ativas existem
        resp_subs = supabase.table("subscriptions").select("status").eq("status", "Ativo").execute()
        active_count = len(resp_subs.data)
        
        # Simulação de faturamento (Ex: R$ 97,00 por oficina ativa)
        # Quando plugar o Asaas/Stripe, isso virá da API deles.
        mensalidade_estimada = 97.00
        receita_recorrente = active_count * mensalidade_estimada
        
        # Puxar o total de OS geradas no sistema inteiro para exibir impacto
        resp_os = supabase.table("os_records").select("id").execute()
        total_os_geradas = len(resp_os.data)
        
        return {
            "active_clients": active_count,
            "mrr": receita_recorrente,
            "total_os": total_os_geradas
        }
    except Exception:
        return None
