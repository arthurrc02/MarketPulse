"""Detector do formato Shopee.

Reconhece o relatório por uma **assinatura** de colunas características —
não pela lista completa do relatório oficial (que passa de 20 colunas e
varia por região/idioma/versão do Seller Center). Ver ADR-060 em
`decisions.md`: um relatório oficial real da Shopee (PT-BR) foi rejeitado
pela estratégia anterior, que exigia um conjunto fixo e completo de colunas
do formato de exemplo — nenhum arquivo real usa exatamente esses nomes.
"""

from etl.detectors.base import MarketplaceDetector
from etl.detectors.signature import concept, matches_signature
from etl.types import Marketplace

#: Cada posição é um conceito da assinatura; basta UMA grafia (PT-BR, EN, ou
#: uma pequena variação) estar presente no arquivo para satisfazê-lo. Exigir
#: 5 conceitos — não dezenas de colunas — é o que torna a detecção
#: resiliente a mudanças de leiaute sem abrir mão de uma assinatura
#: suficientemente característica (evita falso positivo em uma planilha
#: qualquer, que dificilmente teria as 5 simultaneamente).
SIGNATURE: tuple[frozenset[str], ...] = (
    concept("ID do pedido", "Order ID", "Numero do pedido"),
    concept("Status do pedido", "Order Status", "Status"),
    concept("Nome do Produto", "Product Name", "Produto", "Product"),
    concept("Quantidade", "Quantity"),
    concept("Valor Total", "Total Amount", "Preco Unitario", "Unit Price"),
)


class ShopeeDetector(MarketplaceDetector):
    marketplace = Marketplace.SHOPEE

    def matches(self, headers: frozenset[str]) -> bool:
        return matches_signature(headers, SIGNATURE)
