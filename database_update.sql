-- ==========================================
-- SCRIPT DE ATUALIZAÇÃO: CANCELAMENTO E MOTIVOS
-- ==========================================

-- Adiciona campos na tabela de assinaturas
ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN DEFAULT false;

ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;

-- Atualiza os status antigos em inglês para português
UPDATE public.subscriptions SET status = 'Ativo' WHERE status = 'active';
UPDATE public.subscriptions SET status = 'Atrasado' WHERE status = 'past_due';
UPDATE public.subscriptions SET status = 'Cancelado' WHERE status = 'canceled';

UPDATE public.support_tickets SET status = 'Aberto' WHERE status = 'open';
UPDATE public.support_tickets SET status = 'Fechado' WHERE status = 'closed';

-- Altera o default das tabelas para já criar em Português
ALTER TABLE public.subscriptions ALTER COLUMN status SET DEFAULT 'Ativo';
ALTER TABLE public.support_tickets ALTER COLUMN status SET DEFAULT 'Aberto';
