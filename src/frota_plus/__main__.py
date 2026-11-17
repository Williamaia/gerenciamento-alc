"""Sobe o serviço local."""

import uvicorn

from frota_plus.config import get_settings
from frota_plus.main import create_app


def main() -> None:
    settings = get_settings()
    application = create_app(settings)
    uvicorn.run(application, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
