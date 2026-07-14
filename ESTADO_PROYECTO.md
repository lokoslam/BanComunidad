# ESTADO DEL PROYECTO — BanComunidad Intelligence
**Última actualización:** 2 de julio 2026  
**Stack:** Python 3.x · Streamlit · Plotly · SQLite · Pandas

---

## 1. Visión del Producto

BanComunidad Intelligence es un dashboard financiero interno para analizar y proyectar la rentabilidad del **float de tesorería** de comunidades residenciales.  
El float es el saldo que permanece quieto en cuentas corrientes bancarias mientras las comunidades esperan pagar gastos comunes. BanComunidad actúa como gestor de ese capital, invirtiéndolo de forma segura y compartiendo las ganancias con las comunidades.

**Estado actual:** MVP funcional con datos reales de 43 comunidades, 365 días de cartolas.

---

## 2. Estructura de Archivos

```
bancocomunidad-intelligence/
│
├── app/                          # Capa de presentación (Streamlit)
│   ├── Home.py                   # Punto de entrada. Define navegación (st.navigation)
│   ├── styles.py                 # Paleta, CSS global, helpers de layout compartidos
│   └── pages/
│       ├── portada.py            # Landing page con SVG vault + 6 cards de módulos
│       ├── modelo.py             # Cobertura de datos: matriz ✓/⚠/✕ por comunidad × mes
│       ├── resultados.py         # Waterfall capital + evolución temporal + estadísticas
│       ├── simulador.py          # Proyección financiera con sliders (tasa, % invertible, etc.)
│       ├── analisis.py           # Análisis por comunidad + comparativas + saldo por banco
│       ├── mi_comunidad.py       # Vista del administrador: saldo individual + rendimiento
│       ├── inteligencia.py       # Análisis ejecutivo generado con IA (Claude API)
│       ├── carga.py              # ETL manual: carga de Excel → SQLite
│       │
│       ├── 1_Simulador.py        # [LEGADO] Versión antigua del simulador — ignorar
│       └── 2_Analisis_Comunidades.py  # [LEGADO] Versión antigua del análisis — ignorar
│
├── core/                         # Lógica de negocio pura (sin Streamlit)
│   ├── liquidity.py              # resumen_riesgo(), saldo_invertible_dinamico(), P5, CV
│   ├── cobertura.py              # resumen_cobertura(), matriz_cobertura_mensual(), saldo_por_banco()
│   ├── breakeven.py              # Cálculos de ingreso por comunidad y punto de break-even
│   └── formatting.py            # fmt_clp(), fmt_abr(), COLOR_BANCOS, banco_color()
│
├── etl/                          # Scripts de carga de datos
│   ├── import_excel.py           # Importa cartolas Excel → saldos_diarios en SQLite
│   └── import_base_edificios.py  # Importa tabla maestra de edificios → SQLite
│
├── data/
│   └── raw/
│       └── saldos_diarios.db     # Base de datos SQLite (fuente de verdad)
│
├── tests/
│   └── test_liquidity.py         # Tests unitarios para core/liquidity.py
│
├── check.py                      # Script de diagnóstico ad-hoc (no borrar)
├── check2.py                     # Script de diagnóstico ad-hoc (no borrar)
└── ESTADO_PROYECTO.md            # Este archivo
```

---

## 3. Módulos del Dashboard

### Portada (`portada.py`)
- SVG animado tipo "bóveda arquitectónica" con gradiente magenta
- KPI de portada: total administrado, N comunidades, días de datos
- 6 cards de módulos navegables (íconos Material Symbols outline via CDN)
- Cards completamente clickeables via botón invisible overlay (`position:absolute, opacity:0`)

### Modelo (`modelo.py`)
- Bloque descriptivo + 4 mini-stats: comunidades, bancos, admins, unidades
- KPIs de cobertura: edificios totales, con cartolas, pendientes, % completitud a nivel de cartola
- Barra de progreso de cartolas completas (celdas Cargado / posibles)
- Matriz heatmap ✓/⚠/✕ por comunidad × mes (HTML table personalizada)
- Filtro: mostrar solo comunidades con datos incompletos

### Resultados (`resultados.py`)
- **Waterfall** capital: Mínimo histórico → Suma naïve → P5 diversificado → Saldo promedio
- Insight box que explica el beneficio de la diversificación
- **Serie temporal** del saldo agregado diario con fill entre saldo y P5
- Referencias horizontales: P5 (magenta sólido), Promedio (gris punteado), Mínimo (gris punteado)
- Estadísticas de cartera: volatilidad (CV) con tooltip explicativo

### Simulador (`simulador.py`)
- Sliders: N comunidades, saldo promedio, % invertible, tasa anual, % BanComunidad, costos
- Indicador 🟣 en label cuando el slider difiere del valor del modelo real
- Botón "↺ Restablecer" que aparece solo cuando hay modificaciones
- Outputs: ingreso bruto mensual, EBITDA, break-even, revenue split BanComunidad vs comunidades
- Banner de estado (rentable / no rentable)

### Análisis por Comunidad (`analisis.py`)
- Selector de comunidad individual + KPIs propios (promedio, mínimo, P5, % invertible, CV)
- Serie temporal individual con línea dinámica de saldo invertible (sigmoid suavizado)
- Tabla comparativa de todas las comunidades
- Bar chart comparativo Top-N
- **Saldo por banco**: bar chart horizontal, pie chart, line chart mensual
- Saldo por tamaño de edificio (cuartiles)

### Mi Comunidad (`mi_comunidad.py`)
- Vista individual del administrador
- KPIs de saldo actual y rendimiento estimado con BanComunidad

### Inteligencia (`inteligencia.py`)
- Análisis ejecutivo generado por Claude API
- Resumen del portafolio con insights automáticos

### Carga de Datos (`carga.py`)
- Uploader de Excel con preview de 5 filas antes de confirmar
- Muestra estado actual de la BD antes de cargar
- Al confirmar: escribe a SQLite y limpia cache (`st.cache_data.clear()`)

---

## 4. Fuente de Datos

### Base de datos: `data/raw/saldos_diarios.db` (SQLite)

#### Tabla `saldos_diarios`
| Campo         | Tipo    | Descripción                        |
|---------------|---------|------------------------------------|
| comunidad_id  | TEXT    | Nombre de la comunidad             |
| fecha         | DATE    | Fecha del saldo (diario)           |
| saldo         | REAL    | Saldo en CLP                       |

- **15.696 filas** · 43 comunidades · rango 2025-04-01 → 2026-03-31 (365 días)
- Saldo promedio diario: $26.4M · Mínimo: $77K · Máximo: $109.5M

#### Tabla `edificios`
| Campo principal | Descripción                              |
|-----------------|------------------------------------------|
| comunidad_id    | Nombre (FK con saldos_diarios)           |
| banco           | Banco donde tiene la cuenta corriente    |
| admin           | Nombre del administrador                 |
| unidades        | N° de unidades residenciales             |
| rut, direccion, comuna | Datos de identificación          |
| pisos, colabs, calderas | Características físicas          |
| anio_edificio   | Año de construcción                      |
| software        | Software de administración               |
| fondo_reserva   | Si tiene fondo de reserva                |

- **43 edificios** · 3.810 unidades totales (promedio 88.6 por edificio, rango 7–271)

#### Distribución por banco
| Banco     | Comunidades |
|-----------|-------------|
| Chile     | 12          |
| Scotia    | 12          |
| BCI       | 10          |
| Santander | 6           |
| BICE      | 2           |
| Security  | 1           |

#### Distribución por administrador
| Administrador | Comunidades |
|---------------|-------------|
| Álvaro        | 23          |
| Nicolás       | 20          |

### Origen de los datos
- Las cartolas bancarias llegan en **Excel** (una hoja por comunidad o un formato consolidado)
- El ETL `etl/import_excel.py` las procesa y las escribe en `saldos_diarios`
- La tabla `edificios` se cargó desde una base maestra via `etl/import_base_edificios.py`
- La carga manual nueva se hace desde la página **Carga de datos** dentro del dashboard

---

## 5. Decisiones de Arquitectura

### SQLite como fuente de verdad
- Una sola base de datos local — sin servidor, sin configuración de conexiones
- Facilita el despliegue: el archivo `.db` viaja con el proyecto
- Actualización via página de carga en el dashboard o scripts ETL directos

### Separación `core/` vs `app/`
- `core/` contiene lógica de negocio pura (sin imports de Streamlit) → testeable con pytest
- `app/` contiene solo la capa de presentación → puede reemplazarse por otra UI sin tocar la lógica

### `@st.cache_data` con parámetros de invalidación
- Las funciones de cache reciben `_n_sal: int, _n_ed: int` (row counts de las tablas) para que Streamlit invalide el cache automáticamente cuando hay nuevos datos cargados
- Sin esto, el cache se congela y muestra datos viejos aunque se haya subido un Excel nuevo

### Colores de banco definidos localmente en `analisis.py`
- `banco_color()` se define en `analisis.py` con el dict inline (no solo importado de `core.formatting`)
- Razón: Streamlit cachea los módulos en `sys.modules` entre sesiones; si `core.formatting` se edita mientras la app está corriendo, el cambio no se refleja hasta reiniciar el proceso. La definición local garantiza que siempre use la paleta actual.

### Íconos Material Symbols via CDN
- Los íconos en las cards de la Portada se cargan desde `fonts.googleapis.com` (Material Symbols Outlined)
- Se inyectan en HTML via `st.markdown(unsafe_allow_html=True)` con `font-variation-settings` para peso delgado (300)
- Los íconos del sidebar usan la sintaxis nativa de Streamlit `:material/icon_name:` — son los mismos íconos pero gestionados por Streamlit

### Cards clickeables con overlay invisible
- La card visual se renderiza en `st.markdown()` (control total de HTML/CSS)
- Un `st.button("")` vacío se posiciona `position:absolute; top:0; left:0; height:170px` sobre la card
- El botón tiene `opacity:0` — invisible visualmente pero captura el click de Streamlit
- El hover de la columna padre activa el CSS de la card (borde magenta + ícono magenta)

---

## 6. Paleta de Colores y Diseño

### Colores base (tema oscuro)
| Variable    | Hex       | Uso                                      |
|-------------|-----------|------------------------------------------|
| `BG`        | `#191919` | Fondo de la app                          |
| `CARD`      | `#1F1F1F` | Fondo de cards y sidebar                 |
| `CARD_ALT`  | `#232323` | Cards activas / ítem seleccionado        |
| `BORDER`    | `#2A2A2A` | Bordes de cards                          |
| `BORDER2`   | `#333333` | Bordes de botones                        |
| `TEXT`      | `#F4F4F4` | Texto principal                          |
| `MUTED`     | `#8A8A8A` | Texto secundario / labels                |
| `ACCENT`    | `#C054BB` | Magenta — color de marca                 |
| `ACCENT_T`  | `rgba(192,84,187,0.08)` | Tinte positivo en banners  |

### Colores Plotly
| Variable     | Hex       | Uso                                      |
|--------------|-----------|------------------------------------------|
| `PLT_LINE`   | `#E8E8E8` | Barras y líneas principales              |
| `PLT_ACCENT` | `#C054BB` | P5, capital invertible, referencias      |
| `PLT_MUTED`  | `#555555` | Barras secundarias / elementos naïve     |
| `PLT_GRID`   | `rgba(255,255,255,0.05)` | Grilla de gráficos         |

### Paleta de bancos (sobria, armónica con el tema oscuro)
| Banco     | Color     | Tono          |
|-----------|-----------|---------------|
| Chile     | `#4A6FA5` | Azul pizarra  |
| Scotia    | `#C98A3E` | Ámbar apagado |
| BCI       | `#5B8C6E` | Verde salvia  |
| Santander | `#B5484F` | Rojo vino     |
| BICE      | `#4A9BA8` | Teal          |
| Security  | `#7D5A94` | Lila          |
| Itaú      | `#C9782E` | Naranja tierra|

### Principios de diseño aplicados
- **Sin color de fondo en hover** — solo el ícono/borde cambia a magenta (sin bloque de fondo)
- **Ítem activo en sidebar**: fondo `CARD_ALT` + borde izquierdo magenta sólido
- **Tipografía**: sin-serif del sistema; títulos con `letter-spacing` negativo; labels en uppercase 10px
- **Cards**: `border-radius: 12px`, sombra `0 1px 3px rgba(0,0,0,0.5)`
- **Gráficos**: fondo transparente, grilla muy tenue, sin bordes en ejes

---

## 7. Pendientes Conocidos

### Bugs abiertos
- **Módulos legados** (`1_Simulador.py`, `2_Analisis_Comunidades.py`): archivos obsoletos que coexisten con las versiones nuevas. No causan errores pero deberían eliminarse para evitar confusión.
- **Overlay de cards en portada**: la altura `170px` del botón invisible está hardcodeada. Si el texto de descripción de alguna card es muy largo, el área de click no cubre la card entera.

### Mejoras identificadas
- **Carga automática** de cartolas: actualmente manual via Excel. Integración directa con APIs bancarias o un cron que lea un directorio sería el siguiente paso.
- **Exposición Expo Condominios**: la página `carga.py` fue construida pensando en una demo en vivo — preparar datos de demostración (dataset limpio y representativo).
- **Página Mi Comunidad**: es la menos desarrollada de todas. Falta la vista completa del administrador con histórico y proyección individual.
- **Inteligencia**: la página existe pero depende de llamadas a Claude API — evaluar costos y latencia para uso en demo.
- **Tests**: solo existe `test_liquidity.py`. Faltan tests para `core/cobertura.py`, `core/breakeven.py` y los ETL.
- **Encoding UTF-8** en la tabla `edificios`: nombres con acentos (Álvaro, Nicolás) tienen problema de encoding al leer desde SQLite — se ven con `?`. Corregir en el ETL de importación.
- **Deploy**: el botón "Deploy" aparece en la UI de Streamlit. Evaluar Streamlit Community Cloud o despliegue interno con autenticación.

---

## 8. Cómo Correr el Proyecto

```bash
# Instalar dependencias
pip install streamlit plotly pandas anthropic

# Correr el dashboard
streamlit run "app/Home.py"

# Carga de datos (alternativa a la UI)
python etl/import_excel.py

# Tests
pytest tests/
```

La app queda disponible en `http://localhost:8501`.

---

*Generado automáticamente desde el estado del repositorio el 2026-07-02.*
