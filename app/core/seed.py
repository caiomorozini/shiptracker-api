"""
Database seeding functions
"""
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.occurrence_code import OccurrenceCode


OCCURRENCE_CODES_DATA = [
    {"code": "1", "description": "mercadoria entregue", "type": "entrega", "process": "entrega"},
    {"code": "2", "description": "mercadoria pre-entregue (mobile)", "type": "préentrega", "process": "entrega"},
    {"code": "3", "description": "mercadoria devolvida ao remetente", "type": "entrega", "process": "devolução"},
    {"code": "4", "description": "destinatario retira", "type": "pendência cliente", "process": "entrega"},
    {"code": "5", "description": "cliente alega mercad desacordo c/ pedido", "type": "pendência cliente", "process": "entrega"},
    {"code": "7", "description": "chegada no cliente destinatário", "type": "informativa", "process": "entrega"},
    {"code": "9", "description": "destinatario desconhecido", "type": "pendência cliente", "process": "entrega"},
    {"code": "10", "description": "local de entrega nao localizado", "type": "pendência cliente", "process": "entrega"},
    {"code": "11", "description": "local de entrega fechado/ausente", "type": "pendência cliente", "process": "entrega"},
    {"code": "13", "description": "entrega prejudicada pelo horario", "type": "pendência transportadora", "process": "entrega"},
    {"code": "14", "description": "nota fiscal entregue", "type": "pendência cliente", "process": "entrega"},
    {"code": "15", "description": "entrega agendada pelo cliente", "type": "pendência cliente", "process": "agendamento"},
    {"code": "16", "description": "entrega aguardando instrucoes", "type": "pendência cliente", "process": "entrega"},
    {"code": "17", "description": "mercadoria entregue no parceiro", "type": "informativa", "process": "entrega"},
    {"code": "18", "description": "mercad repassada p/ prox transportadora", "type": "entrega", "process": "entrega"},
    {"code": "20", "description": "cliente alega falta de mercadoria", "type": "pendência transportadora", "process": "entrega"},
    {"code": "23", "description": "cliente alega mercadoria avariada", "type": "pendência transportadora", "process": "entrega"},
    {"code": "25", "description": "remetente recusa receber devolução", "type": "pendência cliente", "process": "devolução"},
    {"code": "26", "description": "aguardando autorizacao p/ devolucao", "type": "pendência cliente", "process": "devolução"},
    {"code": "27", "description": "devolucao autorizada", "type": "informativa", "process": "devolução"},
    {"code": "28", "description": "aguardando autorizacao p/ reentrega", "type": "pendência cliente", "process": "reentrega"},
    {"code": "31", "description": "primeira tentativa de entrega", "type": "pendência cliente", "process": "reentrega"},
    {"code": "32", "description": "segunda tentativa de entrega", "type": "pendência cliente", "process": "reentrega"},
    {"code": "33", "description": "terceira tentativa de entrega", "type": "pendência cliente", "process": "reentrega"},
    {"code": "34", "description": "mercadoria em conferencia no cliente", "type": "pendência cliente", "process": "entrega"},
    {"code": "35", "description": "aguardando agendamento do cliente", "type": "pendência cliente", "process": "agendamento"},
    {"code": "36", "description": "mercad em devolucao em outra operacao", "type": "baixa", "process": "devolução"},
    {"code": "37", "description": "entrega realizada com ressalva", "type": "pendência transportadora", "process": "entrega"},
    {"code": "38", "description": "cliente recusa/nao pode receber mercad", "type": "pendência cliente", "process": "entrega"},
    {"code": "39", "description": "cliente recusa pagar o frete", "type": "pendência cliente", "process": "geral"},
    {"code": "40", "description": "frete do ctrc de origem recebido", "type": "informativa", "process": "geral"},
    {"code": "45", "description": "carta sinistrada pendência", "type": "cliente", "process": "geral"},
    {"code": "99", "description": "ctrc baixado/cancelado", "type": "baixa", "process": "geral"},
    {"code": "94", "description": "ctrc substituido", "type": "baixa", "process": "geral"},
    {"code": "93", "description": "ctrc emitido para efeito de frete", "type": "baixa", "process": "geral"},
    {"code": "92", "description": "mercadoria indenizada", "type": "baixa", "process": "indenização"},
    {"code": "91", "description": "mercadoria em indenizacao", "type": "pendência transportadora", "process": "indenização"},
    {"code": "86", "description": "estorno de baixa/entrega anterior", "type": "informativa", "process": "geral"},
    {"code": "85", "description": "saida para entrega", "type": "informativa", "process": "operacional"},
    {"code": "84", "description": "chegada na unidade", "type": "informativa", "process": "operacional"},
    {"code": "83", "description": "chegada em unidade", "type": "informativa", "process": "operacional"},
    {"code": "82", "description": "saida de unidade", "type": "informativa", "process": "operacional"},
    {"code": "80", "description": "mercadoria recebida para transporte", "type": "informativa", "process": "operacional"},
    {"code": "79", "description": "coleta reversa agendada", "type": "informativa", "process": "coleta"},
    {"code": "78", "description": "coleta reversa realizada", "type": "informativa", "process": "coleta"},
    {"code": "77", "description": "coleta cancelada", "type": "informativa", "process": "coleta"},
    {"code": "76", "description": "terceira tentativa de coleta", "type": "informativa", "process": "coleta"},
    {"code": "75", "description": "segunda tentativa de coleta", "type": "informativa", "process": "coleta"},
    {"code": "74", "description": "primeira tentativa de coleta", "type": "informativa", "process": "coleta"},
    {"code": "73", "description": "aguardando disponibilidade de balsa", "type": "informativa", "process": "balsa"},
    {"code": "66", "description": "nova mercad enviada pelo remetente", "type": "informativa", "process": "finalizadora"},
    {"code": "65", "description": "notific remet de envio nova mercad", "type": "pendência transportadora", "process": "finalizadora"},
    {"code": "62", "description": "via interditada por fatores naturais", "type": "pendência cliente", "process": "geral"},
    {"code": "61", "description": "mercadoria confiscada pela fiscalização", "type": "baixa", "process": "finalizadora"},
    {"code": "60", "description": "via interditada", "type": "pendência cliente", "process": "geral"},
    {"code": "59", "description": "veiculo aváriado/sinistrado", "type": "pendência transportadora", "process": "geral"},
    {"code": "58", "description": "mercad liberada pela fiscalizacao", "type": "informativa", "process": "geral"},
    {"code": "57", "description": "greve ou paralizacao", "type": "pendência cliente", "process": "geral"},
    {"code": "56", "description": "mercad retida pela fiscalizacao", "type": "pendência cliente", "process": "geral"},
    {"code": "55", "description": "carga roubada", "type": "pendência cliente", "process": "geral"},
    {"code": "54", "description": "embalagem avariada", "type": "pendência transportadora", "process": "geral"},
    {"code": "53", "description": "mercadoria avariada", "type": "pendência transportadora", "process": "geral"},
    {"code": "52", "description": "falta de documentacao", "type": "pendência transportadora", "process": "geral"},
    {"code": "51", "description": "sobra de mercadoria", "type": "pendência transportadora", "process": "geral"},
    {"code": "50", "description": "falta de mercadoria", "type": "pendência transportadora", "process": "geral"},
]


async def seed_occurrence_codes(session: AsyncSession) -> None:
    """
    Seed occurrence codes table with initial data.
    Only inserts codes that don't exist yet.
    """
    try:
        # Check if any codes already exist
        result = await session.execute(select(OccurrenceCode).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Occurrence codes already seeded, skipping...")
            return
        
        logger.info("Seeding occurrence codes...")
        inserted_count = 0
        
        for code_data in OCCURRENCE_CODES_DATA:
            occurrence_code = OccurrenceCode(**code_data)
            session.add(occurrence_code)
            inserted_count += 1
        
        await session.commit()
        logger.info(f"Successfully seeded {inserted_count} occurrence codes")
        
    except Exception as e:
        logger.error(f"Error seeding occurrence codes: {e}")
        await session.rollback()
        raise
