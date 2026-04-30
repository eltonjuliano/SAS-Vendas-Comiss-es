from typing import List, Dict, Any
from models.commission_rules import CommissionRule, SaleItem

class CommissionEngine:
    """
    Motor flexível para cálculo de comissões.
    """
    def __init__(self, rules: List[CommissionRule]):
        self.rules = rules

    def calculate_for_item(self, item: SaleItem) -> float:
        """
        Calcula a comissão para um único item com base nas regras ativas.
        """
        applicable_rules = [
            r for r in self.rules 
            if r.item_type.lower() in (item.type.lower(), item.name.lower(), '*') 
        ]
        
        # Se houver múltiplas regras (ex: uma '*' e uma específica para o item),
        # prioriza a regra específica (não '*' ). Se houver conflito, pega a primeira específica.
        specific_rules = [r for r in applicable_rules if r.item_type != '*']
        
        if specific_rules:
            rule_to_apply = specific_rules[0]
        elif applicable_rules:
            rule_to_apply = applicable_rules[0]
        else:
            return 0.0 # Nenhuma regra encontrada
            
        # Verifica a condição mínima de valor
        if rule_to_apply.condition_min_value is not None:
            if item.value < rule_to_apply.condition_min_value:
                return 0.0
                
        # Aplica a regra
        if rule_to_apply.rule_type == 'percentage':
            # Ex: 2% -> 2.0 / 100 = 0.02
            return item.value * (rule_to_apply.value / 100.0)
        elif rule_to_apply.rule_type == 'fixed':
            return rule_to_apply.value
            
        return 0.0

    def calculate_total(self, items: List[SaleItem]) -> Dict[str, Any]:
        """
        Calcula a comissão total para uma lista de itens.
        Retorna um detalhamento e o valor total.
        """
        total_commission = 0.0
        item_breakdown = []
        
        for item in items:
            comm = self.calculate_for_item(item)
            total_commission += comm
            item_breakdown.append({
                'item_name': item.name,
                'item_type': item.type,
                'item_value': item.value,
                'commission_earned': comm
            })
            
        return {
            'total_commission': total_commission,
            'breakdown': item_breakdown
        }

# Função Helper para uso rápido
def run_commission_engine(items_data: List[dict], rules_data: List[dict]) -> float:
    """
    Executa o motor de comissões passando listas de dicionários.
    Retorna apenas o valor total da comissão.
    """
    if not rules_data:
        return 0.0
        
    rules = [CommissionRule.from_dict(r) for r in rules_data]
    items = [SaleItem.from_dict(i) for i in items_data]
    
    engine = CommissionEngine(rules)
    result = engine.calculate_total(items)
    return result['total_commission']
