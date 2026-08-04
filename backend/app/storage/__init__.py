"""Armazenamento de arquivos de upload.

Abstração deliberada (`FileStorage`) por trás de uma única implementação
local (`LocalFileStorage`): a Sprint 3 não usa nuvem, mas o motor ETL da
Sprint 4 consome arquivos através desta mesma interface — trocar o backend de
armazenamento (ou adicionar um cache, por exemplo) não deve exigir mudanças
em `UploadService` nem no futuro pipeline ETL.
"""

from app.storage.base import FileStorage
from app.storage.local import LocalFileStorage

__all__ = ["FileStorage", "LocalFileStorage"]
