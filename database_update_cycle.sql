-- ==========================================
-- SCRIPT RÁPIDO: ADICIONAR DATAS FIXAS DE CICLO
-- Cole no SQL Editor do Supabase e clique em Run
-- ==========================================

ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS cycle_start_date TEXT,
ADD COLUMN IF NOT EXISTS cycle_end_date TEXT;
