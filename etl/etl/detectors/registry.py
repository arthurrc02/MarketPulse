"""Registro dos detectores disponíveis e a função pública de detecção."""

from collections.abc import Iterable

from etl.detectors.base import MarketplaceDetector
from etl.detectors.mercado_livre import MercadoLivreDetector
from etl.detectors.shopee import ShopeeDetector
from etl.exceptions import UnknownMarketplaceError
from etl.types import Marketplace

#: Um detector por marketplace suportado nesta sprint. Adicionar um
#: marketplace novo é acrescentar uma linha aqui — nenhum outro módulo do
#: pacote `detectors` muda (ver decisions.md sobre a redução de escopo para
#: 2 formatos de exemplo).
DETECTORS: tuple[MarketplaceDetector, ...] = (ShopeeDetector(), MercadoLivreDetector())


def detect_marketplace(headers: Iterable[str]) -> Marketplace:
    """Identifica o marketplace de origem a partir dos cabeçalhos do arquivo.

    Raises:
        UnknownMarketplaceError: nenhum detector reconheceu os cabeçalhos, ou
            mais de um reconheceu (conjuntos de cabeçalho ambíguos — não
            deveria acontecer com os detectores atuais, cujos conjuntos
            exigidos são disjuntos, mas a checagem é defensiva).
    """
    header_set = frozenset(headers)
    matches = [detector for detector in DETECTORS if detector.matches(header_set)]

    if not matches:
        raise UnknownMarketplaceError(
            "Não foi possível identificar o marketplace de origem a partir "
            "dos cabeçalhos do arquivo. Verifique se o arquivo corresponde "
            "a um formato suportado (Shopee ou Mercado Livre)."
        )
    if len(matches) > 1:
        names = ", ".join(detector.marketplace.value for detector in matches)
        raise UnknownMarketplaceError(
            f"Os cabeçalhos do arquivo correspondem a mais de um marketplace ({names})."
        )
    return matches[0].marketplace
