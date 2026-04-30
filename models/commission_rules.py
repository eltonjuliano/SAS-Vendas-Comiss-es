from typing import List, Optional
from dataclasses import dataclass, asdict

@dataclass
class CommissionRule:
    """
    Representa uma regra de comissão aplicável a um tipo de item.
    """
    id: str
    item_type: str # Ex: 'parts', 'services', 'tires', 'imoveis', 'seguros', '*' para todas
    rule_type: str # 'percentage', 'fixed'
    value: float   # Valor da porcentagem (ex: 2.0 para 2%) ou valor fixo (ex: 50.0 para R$50)
    condition_min_value: Optional[float] = None # Só aplica se valor do item >= X
    
    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', ''),
            item_type=data.get('item_type', '*'),
            rule_type=data.get('rule_type', 'percentage'),
            value=float(data.get('value', 0.0)),
            condition_min_value=float(data.get('condition_min_value')) if data.get('condition_min_value') is not None else None
        )

@dataclass
class SaleItem:
    """
    Representa um item vendido dentro de uma venda (sales_record).
    """
    name: str
    type: str # Ex: 'parts', 'services', 'imoveis'
    value: float
    
    def to_dict(self):
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get('name', ''),
            type=data.get('type', 'general'),
            value=float(data.get('value', 0.0))
        )
