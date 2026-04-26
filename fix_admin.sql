-- ==========================================
-- SCRIPT DE CORREÇÃO: RECURSÃO E ADMIN
-- Cole no SQL Editor e clique em Run
-- ==========================================

-- 1. Criar função segura que burla o RLS para checar se é admin
-- Isso evita o erro de "infinite recursion"
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Deletar as políticas antigas que estavam em loop
DROP POLICY IF EXISTS "Perfis visíveis para o próprio usuário ou para admin" ON public.profiles;
DROP POLICY IF EXISTS "Clientes veem sua própria assinatura" ON public.subscriptions;
DROP POLICY IF EXISTS "Clientes veem/inserem seus chamados" ON public.support_tickets;
DROP POLICY IF EXISTS "Apenas admin pode atualizar chamados (responder)" ON public.support_tickets;

-- 3. Recriar as políticas usando a função segura
CREATE POLICY "Perfis visíveis para o próprio usuário ou para admin"
ON public.profiles FOR SELECT
USING (auth.uid() = id OR public.is_admin());

CREATE POLICY "Clientes veem sua própria assinatura"
ON public.subscriptions FOR SELECT
USING (auth.uid() = user_id OR public.is_admin());

CREATE POLICY "Clientes veem/inserem seus chamados"
ON public.support_tickets FOR SELECT
USING (auth.uid() = user_id OR public.is_admin());

CREATE POLICY "Apenas admin pode atualizar chamados (responder)"
ON public.support_tickets FOR UPDATE
USING (public.is_admin());

-- 4. Definir VOCÊ como Administrador do sistema
-- (Como você criou a conta DEPOIS de rodar o primeiro script, você ficou como 'client')
UPDATE public.profiles 
SET role = 'admin' 
WHERE email = 'eltonjuliano@gmail.com';
