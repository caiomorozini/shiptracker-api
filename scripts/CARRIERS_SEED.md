# Script para seed de carriers

Este script popula o banco de dados com as transportadoras padrão.

## Como usar

```bash
# No diretório do backend
python scripts/seed_carriers.py
```

O script irá criar as seguintes transportadoras padrão:
- SSW
- Correios
- SEDEX
- Jadlog
- Loggi

Se já existirem transportadoras no banco, o script não fará nada.
