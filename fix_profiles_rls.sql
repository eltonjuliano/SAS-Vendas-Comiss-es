-- ==========================================
-- SCRIPT RÁPIDO: CORRIGIR PERMISSÕES DE PERFIL
-- Cole no SQL Editor do Supabase e aperte Run
-- ==========================================

-- Permite que o próprio usuário insira o seu perfil
CREATE POLICY "Usuários podem criar seus próprios perfis" 
ON public.profiles FOR INSERT 
WITH CHECK (auth.uid() = id);

-- Permite que o próprio usuário atualize o seu perfil
CREATE POLICY "Usuários podem atualizar seus próprios perfis" 
ON public.profiles FOR UPDATE 
USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
