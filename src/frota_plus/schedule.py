"""Pedido das 08:00. O processo acorda e chama o serviço."""

import asyncio
import logging
from datetime import datetime

from frota_plus.domain.dates import SAO_PAULO

logger = logging.getLogger("frota_plus.schedule")


async def run_schedule(app) -> None:
    await asyncio.sleep(2)
    while True:
        try:
            app.state.service.tick(datetime.now(SAO_PAULO))
        except Exception:
            logger.exception("agenda")
        await asyncio.sleep(30)
