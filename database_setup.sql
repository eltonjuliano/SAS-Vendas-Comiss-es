-- ==========================================
-- SCRIPT DE CONFIGURAÇÃO DO BANCO DE DADOS
-- Cole este script no "SQL Editor" do Supabase e clique em "Run"
-- ==========================================

-- 1. Tabela de Ordens de Serviço (OS)
CREATE TABLE IF NOT EXISTS public.os_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Vínculo com o usuário dono
    os_number TEXT NOT NULL,
    date DATE,
    entrada_time TEXT,
    autorizacao_time TEXT,
    fechamento_time TEXT,
    saida_time TEXT,
    customer TEXT,
    email TEXT,
    vehicle TEXT,
    vehicle_model TEXT,
    vehicle_year TEXT,
    plate TEXT,
    contact TEXT,
    total_parts NUMERIC DEFAULT 0.0,
    total_services NUMERIC DEFAULT 0.0,
    total_tires NUMERIC DEFAULT 0.0,
    tire_quantity INTEGER DEFAULT 0,
    total_michelin NUMERIC DEFAULT 0.0,
    michelin_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabela de Lançamentos Financeiros (Fluxo Pessoal)
CREATE TABLE IF NOT EXISTS public.finance_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Vínculo com o usuário dono
    data DATE NOT NULL,
    tipo TEXT NOT NULL, -- 'Gasto' ou 'Recebível'
    categoria TEXT NOT NULL,
    descricao TEXT,
    valor NUMERIC DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Configuração de Segurança Nível de Linha (RLS - Row Level Security)
-- Isso garante que um cliente não veja os dados de outro cliente.

-- Ativar RLS nas tabelas
ALTER TABLE public.os_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.finance_records ENABLE ROW LEVEL SECURITY;

-- Políticas para OS
CREATE POLICY "Usuários podem ver apenas suas próprias OS" 
ON public.os_records FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem inserir suas próprias OS" 
ON public.os_records FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuários podem deletar suas próprias OS" 
ON public.os_records FOR DELETE 
USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem atualizar suas próprias OS" 
ON public.os_records FOR UPDATE 
USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Políticas para Financeiro
CREATE POLICY "Usuários podem ver apenas seus lançamentos" 
ON public.finance_records FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem inserir seus lançamentos" 
ON public.finance_records FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuários podem deletar seus lançamentos" 
ON public.finance_records FOR DELETE 
USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem atualizar seus lançamentos" 
ON public.finance_records FOR UPDATE 
USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
