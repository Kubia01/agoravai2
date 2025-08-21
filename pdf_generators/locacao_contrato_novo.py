"""
Gerador de PDF de Locação (nova interface)

Este módulo expõe `gerar_pdf_locacao` e delega a implementação para
`pdf_generators.locacao_contrato`, garantindo compatibilidade com código legado.
"""

# Mantém o import leve. Se falhar, a função wrapper abaixo levanta um erro claro.
try:  # pragma: no cover
    from .locacao_contrato import gerar_pdf_locacao as _impl_gerar_pdf_locacao
except Exception as _import_error:  # fallback com mensagem amigável
    _impl_gerar_pdf_locacao = None  # type: ignore


def gerar_pdf_locacao(dados, output_path):
    """Gera o PDF de Locação usando a implementação estável.

    Parameters
    ----------
    dados : dict
        Dados necessários para preencher o contrato.
    output_path : str
        Caminho do PDF de saída.
    """
    if _impl_gerar_pdf_locacao is None:
        raise ImportError(
            f"Erro ao carregar gerador de PDF de Locação: {_import_error}. "
            "Verifique se as dependências estão instaladas: reportlab, PyPDF2. "
            "Também é necessário ter o LibreOffice disponível no sistema para a conversão do DOCX."
        )
    return _impl_gerar_pdf_locacao(dados, output_path)


__all__ = ["gerar_pdf_locacao"]

