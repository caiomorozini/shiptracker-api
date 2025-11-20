"""
Enums for shipment status
"""
from enum import Enum


class ShipmentStatus(str, Enum):
    """Standardized shipment status values"""
    
    # Status principais
    PENDING = "pending"              # Aguardando postagem
    POSTED = "posted"                # Postado
    IN_TRANSIT = "in_transit"        # Em trânsito
    OUT_FOR_DELIVERY = "out_for_delivery"  # Saiu para entrega
    DELIVERED = "delivered"          # Entregue
    
    # Status de problema
    DELAYED = "delayed"              # Atrasado
    FAILED_DELIVERY = "failed_delivery"  # Tentativa de entrega falhou
    RETURNED = "returned"            # Devolvido ao remetente
    CANCELLED = "cancelled"          # Cancelado
    
    # Status especiais
    HELD = "held"                    # Retido (alfândega, problemas)
    AWAITING_PICKUP = "awaiting_pickup"  # Aguardando retirada
    
    @property
    def label(self) -> str:
        """Get Portuguese label for status"""
        return STATUS_LABELS.get(self.value, self.value)
    
    @property
    def description(self) -> str:
        """Get detailed description in Portuguese"""
        return STATUS_DESCRIPTIONS.get(self.value, "")
    
    @property
    def color(self) -> str:
        """Get color code for frontend display"""
        return STATUS_COLORS.get(self.value, "gray")
    
    @classmethod
    def from_string(cls, value: str) -> "ShipmentStatus":
        """Convert string to enum, handling legacy values"""
        import unicodedata
        
        # Normalize value: lowercase, strip, remove accents, replace spaces with underscore
        normalized = value.lower().strip()
        # Remove accents (NFD = Canonical Decomposition, then filter out combining marks)
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        normalized = normalized.replace(" ", "_")
        
        # Try direct match
        try:
            return cls(normalized)
        except ValueError:
            pass
        
        # Handle legacy values (Portuguese and malformed values)
        legacy_mapping = {
            # Portuguese values (base)
            "em_transito": cls.IN_TRANSIT,
            "transito": cls.IN_TRANSIT,
            "saiu_para_entrega": cls.OUT_FOR_DELIVERY,
            "entregue": cls.DELIVERED,
            "aguardando": cls.PENDING,
            "postado": cls.POSTED,
            "cancelado": cls.CANCELLED,
            "devolvido": cls.RETURNED,
            "atrasado": cls.DELAYED,
            "aguardando_retirada": cls.AWAITING_PICKUP,
            "retido": cls.HELD,
            
            # Malformed long values from Correios/SSW (exact match first)
            "em_transito_para_a_unidade_destino": cls.IN_TRANSIT,
            "em_transito_para_unidade_destino": cls.IN_TRANSIT,
            "objeto_saiu_para_entrega_ao_destinatario": cls.OUT_FOR_DELIVERY,
            "saiu_para_entrega_ao_destinatario": cls.OUT_FOR_DELIVERY,
            "objeto_entregue_ao_destinatario": cls.DELIVERED,
            "entregue_ao_destinatario": cls.DELIVERED,
            "objeto_postado": cls.POSTED,
            "tentativa_de_entrega_nao_realizada": cls.FAILED_DELIVERY,
            "tentativa_nao_realizada": cls.FAILED_DELIVERY,
        }
        
        # Try exact match first
        if normalized in legacy_mapping:
            return legacy_mapping[normalized]
        
        # Check for partial matches (for very long/specific messages)
        # Match if ANY of these keywords appear in the normalized string
        partial_matches = [
            ("entregue", cls.DELIVERED),
            ("saiu_para_entrega", cls.OUT_FOR_DELIVERY),
            ("em_transito", cls.IN_TRANSIT),
            ("transito", cls.IN_TRANSIT),
            ("tentativa", cls.FAILED_DELIVERY),
        ]
        
        for keyword, status in partial_matches:
            if keyword in normalized:
                return status
        
        return cls.PENDING


# Labels em português
STATUS_LABELS: dict[str, str] = {
    "pending": "Aguardando Postagem",
    "posted": "Postado",
    "in_transit": "Em Trânsito",
    "out_for_delivery": "Saiu para Entrega",
    "delivered": "Entregue",
    "delayed": "Atrasado",
    "failed_delivery": "Tentativa de Entrega Falhou",
    "returned": "Devolvido",
    "cancelled": "Cancelado",
    "held": "Retido",
    "awaiting_pickup": "Aguardando Retirada",
}

# Descrições detalhadas
STATUS_DESCRIPTIONS: dict[str, str] = {
    "pending": "A encomenda foi registrada e está aguardando ser postada",
    "posted": "A encomenda foi postada e aceita pela transportadora",
    "in_transit": "A encomenda está em trânsito para o destino",
    "out_for_delivery": "A encomenda saiu para entrega ao destinatário",
    "delivered": "A encomenda foi entregue com sucesso",
    "delayed": "A encomenda está atrasada em relação à previsão",
    "failed_delivery": "Houve uma tentativa de entrega que não foi bem-sucedida",
    "returned": "A encomenda foi devolvida ao remetente",
    "cancelled": "A encomenda foi cancelada",
    "held": "A encomenda está retida (alfândega, documentação, etc)",
    "awaiting_pickup": "A encomenda está disponível para retirada",
}

# Cores para frontend (Tailwind CSS)
STATUS_COLORS: dict[str, str] = {
    "pending": "yellow",
    "posted": "blue",
    "in_transit": "blue",
    "out_for_delivery": "indigo",
    "delivered": "green",
    "delayed": "orange",
    "failed_delivery": "red",
    "returned": "red",
    "cancelled": "gray",
    "held": "orange",
    "awaiting_pickup": "purple",
}


def get_all_statuses():
    """Get all available statuses with metadata"""
    return [
        {
            "value": status.value,
            "label": status.label,
            "description": status.description,
            "color": status.color
        }
        for status in ShipmentStatus
    ]
