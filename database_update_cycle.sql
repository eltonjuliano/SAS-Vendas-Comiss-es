-- =========================================================================
-- ATUALIZAÇÃO DO BANCO DE DADOS: CICLO DE COMISSÕES (DATA PERSONALIZADA)
-- Copie este script e cole no "SQL Editor" do Supabase, depois clique em Run.
-- =========================================================================

-- Adiciona as colunas de configuração de dias de faturamento na tabela profiles
-- Por padrão, começará no dia 1 e terminará no dia 31, mas o usuário poderá alterar na tela 'Minha Conta'.
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS cycle_start_day INTEGER DEFAULT 1;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS cycle_end_day INTEGER DEFAULT 31;
