-- ==========================================
-- SCRIPT DE ATUALIZAÇÃO DO BANCO DE DADOS - COMIFYX
-- Cole este script no "SQL Editor" do Supabase e clique em "Run"
-- ATENÇÃO: Faça um backup da sua tabela os_records antes de rodar, por precaução.
-- ==========================================

-- 1. Atualizar Tabela de Perfis
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS profile_type TEXT DEFAULT 'Auto Center',
ADD COLUMN IF NOT EXISTS commission_rules JSONB DEFAULT '[]'::jsonb;

-- 2. Criar a nova tabela genérica de Vendas (sales_records)
CREATE TABLE IF NOT EXISTS public.sales_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    identifier TEXT NOT NULL, -- Ex: Número da OS, Número do Pedido, ID da Venda
    date DATE,
    client TEXT,
    total_value NUMERIC DEFAULT 0.0,
    items JSONB DEFAULT '[]'::jsonb, -- Lista de itens vendidos [{nome, valor, tipo}]
    total_commission NUMERIC DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb, -- Dados extras baseados no perfil (placa, chassi, etc)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Ativar RLS e Políticas para sales_records
ALTER TABLE public.sales_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários podem ver apenas suas próprias vendas" 
ON public.sales_records FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem inserir suas próprias vendas" 
ON public.sales_records FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuários podem deletar suas próprias vendas" 
ON public.sales_records FOR DELETE 
USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem atualizar suas próprias vendas" 
ON public.sales_records FOR UPDATE 
USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- 4. Migrar dados de os_records para sales_records (Preservando IDs)
-- Obs: Usamos ON CONFLICT DO NOTHING para caso você rode este script duas vezes
INSERT INTO public.sales_records (id, user_id, identifier, date, client, total_value, items, total_commission, metadata, created_at)
SELECT 
    id, 
    user_id, 
    os_number as identifier, 
    date, 
    customer as client, 
    (total_parts + total_services) as total_value, 
    jsonb_build_array(
        jsonb_build_object('name', 'Peças', 'value', GREATEST(0, total_parts - total_tires), 'type', 'parts'),
        jsonb_build_object('name', 'Serviços', 'value', total_services, 'type', 'services'),
        jsonb_build_object('name', 'Pneus', 'value', total_tires, 'type', 'tires')
    ) as items,
    0.0 as total_commission, -- Comissão será recalculada pela nova engine caso necessário, ou calculada em tempo de execução
    jsonb_build_object(
        'email', email,
        'vehicle', vehicle,
        'vehicle_model', vehicle_model,
        'vehicle_year', vehicle_year,
        'plate', plate,
        'contact', contact,
        'tire_quantity', tire_quantity,
        'total_michelin', total_michelin,
        'michelin_quantity', michelin_quantity,
        'entrada_time', entrada_time,
        'autorizacao_time', autorizacao_time,
        'fechamento_time', fechamento_time,
        'saida_time', saida_time
    ) as metadata,
    created_at
FROM public.os_records
ON CONFLICT (id) DO NOTHING;

-- Nota: Após validar que os dados estão corretos em sales_records, 
-- a tabela os_records pode ser deletada no futuro.
