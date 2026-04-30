import unittest
from models.commission_rules import CommissionRule, SaleItem
from services.commission_engine import CommissionEngine, run_commission_engine

class TestCommissionEngine(unittest.TestCase):
    def test_percentage_rule(self):
        rules = [
            CommissionRule(id="1", item_type="parts", rule_type="percentage", value=5.0) # 5%
        ]
        items = [
            SaleItem(name="Pastilha de freio", type="parts", value=100.0)
        ]
        engine = CommissionEngine(rules)
        result = engine.calculate_total(items)
        
        self.assertEqual(result['total_commission'], 5.0)

    def test_fixed_rule(self):
        rules = [
            CommissionRule(id="1", item_type="services", rule_type="fixed", value=50.0) # R$50 fixo
        ]
        items = [
            SaleItem(name="Alinhamento", type="services", value=200.0)
        ]
        engine = CommissionEngine(rules)
        result = engine.calculate_total(items)
        
        self.assertEqual(result['total_commission'], 50.0)

    def test_wildcard_rule(self):
        rules = [
            CommissionRule(id="1", item_type="*", rule_type="percentage", value=10.0) # 10% geral
        ]
        items = [
            SaleItem(name="Qualquer", type="unknown", value=150.0),
            SaleItem(name="Outro", type="parts", value=50.0)
        ]
        engine = CommissionEngine(rules)
        result = engine.calculate_total(items)
        
        # 10% de 200 = 20
        self.assertEqual(result['total_commission'], 20.0)

    def test_rule_priority(self):
        rules = [
            CommissionRule(id="1", item_type="*", rule_type="percentage", value=10.0), # 10% geral
            CommissionRule(id="2", item_type="tires", rule_type="percentage", value=2.0) # 2% apenas pneus
        ]
        items = [
            SaleItem(name="Serviço", type="services", value=100.0), # Cai no wildcard (10)
            SaleItem(name="Pneu", type="tires", value=100.0) # Cai na especifica (2)
        ]
        engine = CommissionEngine(rules)
        result = engine.calculate_total(items)
        
        self.assertEqual(result['total_commission'], 12.0)

    def test_minimum_value_condition(self):
        rules = [
            CommissionRule(id="1", item_type="parts", rule_type="fixed", value=10.0, condition_min_value=50.0) 
        ]
        items = [
            SaleItem(name="Filtro", type="parts", value=40.0), # Não ganha
            SaleItem(name="Óleo", type="parts", value=60.0)    # Ganha 10
        ]
        engine = CommissionEngine(rules)
        result = engine.calculate_total(items)
        
        self.assertEqual(result['total_commission'], 10.0)

    def test_helper_function(self):
        rules_data = [
            {"id": "1", "item_type": "parts", "rule_type": "percentage", "value": 5.0}
        ]
        items_data = [
            {"name": "Peca1", "type": "parts", "value": 200.0}
        ]
        total = run_commission_engine(items_data, rules_data)
        self.assertEqual(total, 10.0)

if __name__ == '__main__':
    unittest.main()
