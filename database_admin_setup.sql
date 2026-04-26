-- ==========================================
-- SCRIPT: ÁREA ADMINISTRATIVA E SUPORTE
-- Cole no SQL Editor do Supabase e clique em Run
-- ==========================================

-- 1. Tabela de Perfis Públicos (para o admin ver nomes e emails facilmente)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    role TEXT DEFAULT 'client', -- 'client' ou 'admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar RLS nos perfis
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Perfis visíveis para o próprio usuário ou para admin"
ON public.profiles FOR SELECT
USING (auth.uid() = id OR (SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin');

-- Atualizar ou inserir perfis para usuários que JÁ EXISTEM
INSERT INTO public.profiles (id, email, display_name)
SELECT id, email, raw_user_meta_data->>'display_name'
FROM auth.users
ON CONFLICT (id) DO NOTHING;

-- Definir Elton como Admin (MUDE O EMAIL ABAIXO SE NECESSÁRIO)
UPDATE public.profiles SET role = 'admin' WHERE email = 'eltonjuliano@gmail.com';

-- Trigger para criar perfil automaticamente quando um NOVO usuário se cadastrar
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, display_name)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'display_name');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Excluir a trigger se ela já existir para evitar erro ao rodar duas vezes
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();


-- 2. Tabela de Assinaturas (Mensalidades - Preparada para gateway futuro)
CREATE TABLE IF NOT EXISTS public.subscriptions (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    status TEXT DEFAULT 'active', -- active, past_due, canceled
    plan_name TEXT DEFAULT 'Plano Básico',
    gateway_customer_id TEXT, -- Para o futuro Asaas/Stripe
    next_billing_date DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Assinaturas
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Clientes veem sua própria assinatura"
ON public.subscriptions FOR SELECT
USING (auth.uid() = user_id OR (SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin');

-- Criar assinatura para usuários existentes que não tem
INSERT INTO public.subscriptions (user_id)
SELECT id FROM public.profiles
ON CONFLICT (user_id) DO NOTHING;

-- 3. Tabela de Tickets de Suporte
CREATE TABLE IF NOT EXISTS public.support_tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    admin_reply TEXT,
    status TEXT DEFAULT 'open', -- open, closed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    replied_at TIMESTAMP WITH TIME ZONE
);

-- RLS Suporte
ALTER TABLE public.support_tickets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Clientes veem/inserem seus chamados"
ON public.support_tickets FOR SELECT
USING (auth.uid() = user_id OR (SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin');

CREATE POLICY "Clientes podem criar chamados"
ON public.support_tickets FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Apenas admin pode atualizar chamados (responder)"
ON public.support_tickets FOR UPDATE
USING ((SELECT role FROM public.profiles WHERE id = auth.uid()) = 'admin');
