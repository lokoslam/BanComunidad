"""
core/formatting.py

Funciones de formato numérico compartidas entre todas las páginas.
"""

from __future__ import annotations


def fmt_clp(valor: float) -> str:
    """Formato CLP completo: $1.234.567"""
    sign = "-" if valor < 0 else ""
    return f"{sign}${abs(valor):,.0f}".replace(",", ".")


def fmt_abr(valor: float) -> str:
    """
    Formato abreviado para KPIs grandes — más legible en pantalla pequeña.
      >= 1.000.000.000  →  $1.02B
      >= 1.000.000      →  $885.69M
      < 1.000.000       →  formato completo ($234.567)
    """
    sign = "-" if valor < 0 else ""
    abs_v = abs(valor)
    if abs_v >= 1_000_000_000:
        return f"{sign}${abs_v / 1_000_000_000:.2f}B"
    if abs_v >= 1_000_000:
        return f"{sign}${abs_v / 1_000_000:.2f}M"
    return fmt_clp(valor)


def fmt_pct(valor: float, decimals: int = 1) -> str:
    """Porcentaje: 0.866 → '86.6%'"""
    return f"{valor * 100:.{decimals}f}%"


# Colores institucionales de cada banco — usar en TODOS los gráficos agrupados por banco
COLOR_BANCOS: dict[str, str] = {
    "Chile":     "#4A6FA5",
    "Itaú":      "#C9782E",
    "Scotia":    "#C98A3E",
    "Santander": "#B5484F",
    "BCI":       "#5B8C6E",
    "BICE":      "#4A9BA8",
    "Security":  "#7D5A94",
}
_BCI_BORDER = "#5B8C6E"   # BCI ahora es verde apagado, no necesita stroke de contraste


def banco_color(nombre: str) -> str:
    """Devuelve el color institucional del banco; fallback gris si no está mapeado."""
    return COLOR_BANCOS.get(nombre, "#6A6A6A")
