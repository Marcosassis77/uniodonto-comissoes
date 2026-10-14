from decimal import Decimal, ROUND_HALF_UP

def calcular_comissao(valor_bruto_str, taxa_str='0.50'):
    try:
        valor = Decimal(str(valor_bruto_str))
        taxa = Decimal(str(taxa_str))
        if valor < 0:
            raise ValueError("Valor da venda não pode ser negativo.")
        return (valor * taxa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception as e:
        raise ValueError(f"Erro no cálculo financeiro: {str(e)}")
