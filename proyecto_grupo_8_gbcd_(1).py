import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(
    page_title="Dashboard Bank Marketing - EDA",
    layout="wide"
)

st.title("Análisis EDA: Factores Determinantes de Suscripción al Plazo Fijo")
st.write("Proyecto Integrador UTEC - Grupo 8")
st.markdown("---")

@st.cache_data
def cargar_datos():
    return pd.read_csv('bank-full.csv', sep=';')

try:
    df_raw = cargar_datos()

    # PALETA MONOCROMÁTICA
    COLOR_NO = '#D1D5DB'   # Gris claro para "no"
    COLOR_SI = '#374151'   # Gris oscuro para "yes"

    # BARRA LATERAL: FILTROS GLOBALES
    st.sidebar.header("Filtros de Exploración")

    trabajos_disponibles = sorted(df_raw['job'].unique().tolist())
    trabajos_sel = st.sidebar.multiselect("Ocupación / Trabajo:", trabajos_disponibles, default=trabajos_disponibles)

    marital_disponibles = sorted(df_raw['marital'].unique().tolist())
    marital_sel = st.sidebar.multiselect("Estado Civil:", marital_disponibles, default=marital_disponibles)

    educacion_disponibles = sorted(df_raw['education'].unique().tolist())
    educacion_sel = st.sidebar.multiselect("Nivel Educativo:", educacion_disponibles, default=educacion_disponibles)

    edad_min, edad_max = int(df_raw['age'].min()), int(df_raw['age'].max())
    rango_edad = st.sidebar.slider("Rango de Edad:", edad_min, edad_max, (edad_min, edad_max))

    df = df_raw[
        (df_raw['job'].isin(trabajos_sel)) &
        (df_raw['marital'].isin(marital_sel)) &
        (df_raw['education'].isin(educacion_sel)) &
        (df_raw['age'].between(rango_edad[0], rango_edad[1]))
    ]

    # KPIs PRINCIPALES
    total_clientes = len(df)
    total_yes = len(df[df['y'] == 'yes'])
    tasa_conversion_global = (total_yes / total_clientes * 100) if total_clientes > 0 else 0
    balance_promedio = df['balance'].mean() if total_clientes > 0 else 0

    def crear_kpi_card(titulo, valor):
        return f"""
        <div style="
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-top: 4px solid #374151;
            border-radius: 8px;
            padding: 16px 12px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            margin-bottom: 10px;
        ">
            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #475569;">{titulo}</p>
            <h2 style="margin: 6px 0 0 0; font-size: 32px; font-weight: 700; color: #0F172A;">{valor}</h2>
        </div>
        """

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(crear_kpi_card("Clientes filtrados", f"{total_clientes:,}"), unsafe_allow_html=True)
    with c2:
        st.markdown(crear_kpi_card("Suscripciones ('yes')", f"{total_yes:,}"), unsafe_allow_html=True)
    with c3:
        st.markdown(crear_kpi_card("Tasa de conversión global", f"{tasa_conversion_global:.2f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(crear_kpi_card("Balance promedio", f"€{balance_promedio:,.0f}"), unsafe_allow_html=True)

    st.markdown("---")

    # SELECCIÓN Y CLASIFICACIÓN DE VARIABLES
    st.header("Suscripción por variable")

    tipo_variable = st.radio(
        "Seleccione Clasificación de Variable:",
        ["Variables Cualitativas (Categóricas)", "Variables Cuantitativas (Numéricas)"],
        horizontal=True
    )

    # ---------------------------------------------------------
    # RAMA 1: CUALITATIVAS
    # ---------------------------------------------------------
    if tipo_variable == "Variables Cualitativas (Categóricas)":
        dict_cualitativas = {
            "Ocupación (job)": "job",
            "Estado Civil (marital)": "marital",
            "Nivel Educativo (education)": "education",
            "Crédito en Default (default)": "default",
            "Crédito Hipotecario (housing)": "housing",
            "Crédito Personal (loan)": "loan",
            "Medio de Contacto (contact)": "contact",
            "Mes de Contacto (month)": "month",
            "Resultado Campaña Previa (poutcome)": "poutcome"
        }
        var_label = st.selectbox("Elegí la variable categórica:", list(dict_cualitativas.keys()))
        var_col = dict_cualitativas[var_label]

        if not df.empty:
            df_counts = df.groupby([var_col, 'y']).size().unstack(fill_value=0).reset_index()
            if 'yes' not in df_counts.columns: df_counts['yes'] = 0
            if 'no' not in df_counts.columns: df_counts['no'] = 0

            df_counts['Total'] = df_counts['yes'] + df_counts['no']
            df_counts['Tasa_Exito_%'] = (df_counts['yes'] / df_counts['Total'] * 100).round(1)
            df_counts['Texto_Porcentaje'] = df_counts['Tasa_Exito_%'].astype(str) + '%'

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Frecuencia absoluta")
                df_melt = df_counts.melt(id_vars=[var_col], value_vars=['no', 'yes'], var_name='¿Suscribió?', value_name='Número de clientes')

                fig_abs = px.bar(
                    df_melt,
                    x=var_col,
                    y='Número de clientes',
                    color='¿Suscribió?',
                    barmode='group',
                    text_auto=',d',
                    template='plotly_white',
                    color_discrete_map={'yes': COLOR_SI, 'no': COLOR_NO},
                    labels={var_col: var_col, 'Número de clientes': 'Número de clientes'}
                )
                fig_abs.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
                fig_abs.update_layout(
                    margin=dict(l=10, r=10, t=30, b=20),
                    xaxis=dict(tickangle=-35),
                    legend_title_text='¿Suscribió?'
                )
                st.plotly_chart(fig_abs, use_container_width=True)

            with col2:
                st.subheader("Porcentaje (tasa de conversión)")
                df_sorted = df_counts.sort_values(by='Tasa_Exito_%', ascending=False)

                fig_pct = px.bar(
                    df_sorted,
                    x=var_col,
                    y='Tasa_Exito_%',
                    color='Tasa_Exito_%',
                    text='Texto_Porcentaje',
                    color_continuous_scale=['#D1D5DB', '#6B7280', '#1F2937'],
                    template='plotly_white',
                    labels={var_col: var_col, 'Tasa_Exito_%': '% que suscribió'}
                )
                fig_pct.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
                fig_pct.update_layout(
                    margin=dict(l=10, r=10, t=30, b=20),
                    xaxis=dict(tickangle=-35),
                    coloraxis_showscale=True,
                    yaxis=dict(range=[0, max(df_sorted['Tasa_Exito_%'].max() * 1.2, 10)])
                )
                st.plotly_chart(fig_pct, use_container_width=True)

            # BLOQUE DE CONCLUSIONES AUTOMÁTICAS
            top_conv = df_counts.sort_values(by='Tasa_Exito_%', ascending=False).iloc[0]
            top_vol = df_counts.sort_values(by='Total', ascending=False).iloc[0]
            diff_media = round(top_conv['Tasa_Exito_%'] - tasa_conversion_global, 1)

            st.markdown(f"""
            <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 16px; border-radius: 6px; margin: 15px 0;">
                <h4 style="margin:0 0 8px 0; color: #15803D;">💡 Hallazgos Clave para {var_label}</h4>
                <ul style="margin: 0; padding-left: 20px; color: #166534; font-size: 15px;">
                    <li><b>Mayor efectividad de conversión:</b> El segmento <b>{top_conv[var_col]}</b> alcanza una conversión del <b>{top_conv['Tasa_Exito_%']}%</b> ({'＋' if diff_media >= 0 else ''}{diff_media} puntos porcentuales respecto al promedio global de {tasa_conversion_global:.1f}%).</li>
                    <li><b>Mayor concentración de volumen:</b> La mayor parte del público objetivo contactado corresponde a <b>{top_vol[var_col]}</b> con <b>{top_vol['Total']:,} clientes</b> (representando el {(top_vol['Total']/total_clientes*100):.1f}% de la muestra).</li>
                    <li><b>Conclusión rápida:</b> Aunque {top_vol[var_col]} aporta volumen, enfocar esfuerzos comerciales en {top_conv[var_col]} incrementará significativamente el ROI de la campaña.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.subheader(f"Resumen Numérico EDA - {var_label}")
            df_tabla = df_counts.sort_values(by='Tasa_Exito_%', ascending=False)[
                [var_col, 'yes', 'no', 'Total', 'Tasa_Exito_%']
            ].rename(columns={'yes': 'Suscripciones (Sí)', 'no': 'No Suscritos (No)', 'Tasa_Exito_%': 'Tasa de Conversión (%)'})
            st.dataframe(df_tabla, use_container_width=True)

    # ---------------------------------------------------------
    # RAMA 2: CUANTITATIVAS
    # ---------------------------------------------------------
    else:
        dict_cuantitativas = {
            "Edad (age)": "age",
            "Balance Anual en Euros (balance)": "balance",
            "Duración del Contacto en Segundos (duration)": "duration",
            "Contactos en esta Campaña (campaign)": "campaign",
            "Días desde Campaña Previa (pdays)": "pdays",
            "Contactos Previos (previous)": "previous"
        }
        var_label = st.selectbox("Elegí la variable numérica:", list(dict_cuantitativas.keys()))
        var_col = dict_cuantitativas[var_label]

        if not df.empty:
            df_num = df.copy()

            if var_col == 'age':
                bins = [-np.inf, 25, 35, 50, 60, np.inf]
                labels = ['<25 años', '25-35 años', '36-50 años', '51-60 años', '>60 años']
            elif var_col == 'balance':
                bins = [-np.inf, 0, 500, 2000, np.inf]
                labels = ['Saldo < 0 €', '0 - 500 €', '500 - 2.000 €', '> 2.000 €']
            elif var_col == 'duration':
                bins = [-np.inf, 120, 300, 600, np.inf]
                labels = ['<2 min', '2-5 min', '5-10 min', '>10 min']
            elif var_col == 'campaign':
                bins = [-np.inf, 1, 2, 4, np.inf]
                labels = ['1 contacto', '2 contactos', '3-4 contactos', '5+ contactos']
            elif var_col == 'pdays':
                bins = [-np.inf, -0.5, 90, 180, 360, np.inf]
                labels = ['Sin contacto (-1)', '0-90 días', '91-180 días', '181-360 días', '>360 días']
            elif var_col == 'previous':
                bins = [-np.inf, 0, 1, 3, np.inf]
                labels = ['0 contactos', '1 contacto', '2-3 contactos', '4+ contactos']

            df_num['Rango'] = pd.cut(df_num[var_col], bins=bins, labels=labels, right=True)

            df_counts = df_num.groupby(['Rango', 'y'], observed=False).size().unstack(fill_value=0).reset_index()
            if 'yes' not in df_counts.columns: df_counts['yes'] = 0
            if 'no' not in df_counts.columns: df_counts['no'] = 0

            df_counts['Total'] = df_counts['yes'] + df_counts['no']
            df_counts['Tasa_Exito_%'] = np.where(df_counts['Total'] > 0, (df_counts['yes'] / df_counts['Total'] * 100).round(1), 0)
            df_counts['Texto_Porcentaje'] = df_counts['Tasa_Exito_%'].astype(str) + '%'

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Frecuencia absoluta")
                df_melt = df_counts.melt(id_vars=['Rango'], value_vars=['no', 'yes'], var_name='¿Suscribió?', value_name='Número de clientes')

                fig_abs = px.bar(
                    df_melt,
                    x='Rango',
                    y='Número de clientes',
                    color='¿Suscribió?',
                    barmode='group',
                    text_auto=',d',
                    template='plotly_white',
                    color_discrete_map={'yes': COLOR_SI, 'no': COLOR_NO},
                    labels={'Rango': var_label, 'Número de clientes': 'Número de clientes'}
                )
                fig_abs.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
                fig_abs.update_layout(
                    margin=dict(l=10, r=10, t=30, b=20),
                    xaxis=dict(tickangle=-25),
                    legend_title_text='¿Suscribió?'
                )
                st.plotly_chart(fig_abs, use_container_width=True)

            with col2:
                st.subheader("Porcentaje (tasa de conversión)")

                fig_pct = px.bar(
                    df_counts,
                    x='Rango',
                    y='Tasa_Exito_%',
                    color='Tasa_Exito_%',
                    text='Texto_Porcentaje',
                    color_continuous_scale=['#D1D5DB', '#6B7280', '#1F2937'],
                    template='plotly_white',
                    labels={'Rango': var_label, 'Tasa_Exito_%': '% que suscribió'}
                )
                fig_pct.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
                fig_pct.update_layout(
                    margin=dict(l=10, r=10, t=30, b=20),
                    xaxis=dict(tickangle=-25),
                    coloraxis_showscale=True,
                    yaxis=dict(range=[0, max(df_counts['Tasa_Exito_%'].max() * 1.2, 10)])
                )
                st.plotly_chart(fig_pct, use_container_width=True)

            # BLOQUE DE CONCLUSIONES AUTOMÁTICAS
            top_conv = df_counts.sort_values(by='Tasa_Exito_%', ascending=False).iloc[0]
            top_vol = df_counts.sort_values(by='Total', ascending=False).iloc[0]
            diff_media = round(top_conv['Tasa_Exito_%'] - tasa_conversion_global, 1)

            st.markdown(f"""
            <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 16px; border-radius: 6px; margin: 15px 0;">
                <h4 style="margin:0 0 8px 0; color: #15803D;">💡 Hallazgos Clave para {var_label}</h4>
                <ul style="margin: 0; padding-left: 20px; color: #166534; font-size: 15px;">
                    <li><b>Rango con mayor conversión:</b> El rango <b>{top_conv['Rango']}</b> presenta la mayor tasa de aceptación con un <b>{top_conv['Tasa_Exito_%']}%</b> ({'＋' if diff_media >= 0 else ''}{diff_media}% comparado a la media global del {tasa_conversion_global:.1f}%).</li>
                    <li><b>Volumen concentrado:</b> La mayor parte de los registros ({top_vol['Total']:,} personas, el {(top_vol['Total']/total_clientes*100):.1f}% del total) se ubica en el rango <b>{top_vol['Rango']}</b>.</li>
                    <li><b>Lectura de negocio:</b> Existe una oportunidad clara al priorizar la gestión en el segmento <b>{top_conv['Rango']}</b>, que convierte sensiblemente por encima del promedio del banco.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.subheader(f"Resumen Numérico EDA - {var_label}")
            df_tabla = df_counts[
                ['Rango', 'yes', 'no', 'Total', 'Tasa_Exito_%']
            ].rename(columns={
                'Rango': f'Rango de {var_label}',
                'yes': 'Suscripciones (Sí)',
                'no': 'No Suscritos (No)',
                'Tasa_Exito_%': 'Tasa de Conversión (%)'
            })
            st.dataframe(df_tabla, use_container_width=True)

    # ==========================================
    # SECCIÓN MULTIVARIADA
    # ==========================================
    st.markdown("---")
    st.header("Análisis Multivariado: Cruces Cualitativos")
    st.caption("Evaluación de la tasa de suscripción combinando múltiples dimensiones.")

    df_temp = df.copy()
    df_temp['target_num'] = (df_temp['y'] == 'yes').astype(int)

    # CRUCE 1: Ocupación vs Estado Civil
    st.subheader("1. Tasa de Conversión (%) por Ocupación y Estado Civil")
    df_cruce1 = df_temp.groupby(['job', 'marital'], observed=False)['target_num'].mean().reset_index()
    df_cruce1['Tasa_%'] = (df_cruce1['target_num'] * 100).round(1)

    fig_m1 = px.bar(
        df_cruce1,
        x='job',
        y='Tasa_%',
        color='marital',
        barmode='group',
        text='Tasa_%',
        color_discrete_sequence=['#252525', '#636363', '#969696', '#cccccc'],
        template='plotly_white',
        labels={'job': 'Ocupación', 'Tasa_%': 'Tasa de Conversión (%)', 'marital': 'Estado Civil'}
    )
    fig_m1.update_traces(textposition='outside', textfont_size=10)
    fig_m1.update_layout(margin=dict(l=10, r=10, t=30, b=20), xaxis=dict(tickangle=-35))
    st.plotly_chart(fig_m1, use_container_width=True)

    # CRUCE 2: Nivel Educativo vs Crédito Hipotecario
    st.subheader("2. Tasa de Conversión (%) por Educación y Crédito Hipotecario")
    df_cruce2 = df_temp.groupby(['education', 'housing'], observed=False)['target_num'].mean().reset_index()
    df_cruce2['Tasa_%'] = (df_cruce2['target_num'] * 100).round(1)

    fig_m2 = px.bar(
        df_cruce2,
        x='education',
        y='Tasa_%',
        color='housing',
        barmode='group',
        text='Tasa_%',
        color_discrete_sequence=['#252525', '#969696'],
        template='plotly_white',
        labels={'education': 'Nivel Educativo', 'Tasa_%': 'Tasa de Conversión (%)', 'housing': 'Tiene Hipoteca'}
    )
    fig_m2.update_traces(textposition='outside', textfont_size=10)
    fig_m2.update_layout(margin=dict(l=10, r=10, t=30, b=20))
    st.plotly_chart(fig_m2, use_container_width=True)

    # CRUCE 3: Canal de Contacto vs Resultado Campaña Previa
    st.subheader("3. Tasa de Conversión (%) por Canal de Contacto y Resultado Previo")
    df_cruce3 = df_temp.groupby(['contact', 'poutcome'], observed=False)['target_num'].mean().reset_index()
    df_cruce3['Tasa_%'] = (df_cruce3['target_num'] * 100).round(1)

    fig_m3 = px.bar(
        df_cruce3,
        x='contact',
        y='Tasa_%',
        color='poutcome',
        barmode='group',
        text='Tasa_%',
        color_discrete_sequence=['#252525', '#636363', '#969696', '#cccccc'],
        template='plotly_white',
        labels={'contact': 'Canal de Contacto', 'Tasa_%': 'Tasa de Conversión (%)', 'poutcome': 'Resultado Previo'}
    )
    fig_m3.update_traces(textposition='outside', textfont_size=10)
    fig_m3.update_layout(margin=dict(l=10, r=10, t=30, b=20))
    st.plotly_chart(fig_m3, use_container_width=True)

    st.markdown("---")
    st.subheader("Muestra de Datos Filtrados")
    st.dataframe(df.head(10), use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

from google.colab import drive
drive.mount('/content/drive')

ruta = '/content/drive/MyDrive/Colab Notebooks/'

df = pd.read_csv(ruta + 'bank-full.csv', sep=';')

data = df.copy()

data.head()

data.tail()

data.shape

data.info()

"""**¿Qué nos dice esto?**

El dataset tiene **45,211 filas** (cada fila = un cliente contactado) y **17 columnas** (características del cliente + el resultado).

- Las columnas `age`, `balance`, `day`, `duration`, `campaign`, `pdays` y `previous` son **números**.
- El resto de las columnas (como `job`, `marital`, `education`) son **texto o categorías**.
- Ninguna columna tiene valores vacíos (los "Non-Null Count" son todos iguales a 45,211), así que **no tenemos datos faltantes**.
"""

data.isna().sum()

"""**Confirmación:** todas las columnas dan 0, es decir, no hay ningún valor vacío en todo el dataset."""

tabla = pd.DataFrame({
    'count': df['y'].value_counts(),
    'percentage': (
        df['y'].value_counts(normalize=True) * 100
    ).round(2)
})
tabla

"""**¿Qué nos dice esto?**

De los 45,211 clientes contactados:
- **39,922 (88.3%) dijeron que NO** querían el depósito.
- **5,289 (11.7%) dijeron que SÍ** y suscribieron.

Esto se llama un **dataset desbalanceado**: hay muchos más "no" que "yes". Esto es normal en campañas de ventas reales — no todos los clientes aceptan. Pero hay que tenerlo en cuenta cuando construyamos el modelo, porque un modelo que prediga "no" siempre acertaría el 88% de las veces sin aprender nada útil.
"""

data.describe().round(3)

"""**¿Qué nos dice esta tabla?**

Esta tabla resume las columnas numéricas. Dos valores importantes:
- **mean** = promedio (media): suma de todos los valores dividido la cantidad.
- **50%** = mediana: el valor del medio si ordenamos todos los datos.

Cuando el promedio es mucho mayor que la mediana, significa que hay algunos valores muy altos que "jalan" el promedio hacia arriba, pero la mayoría de los clientes está cerca de la mediana.

Ejemplos:
- `balance`: promedio = 1,362 EUR pero mediana = 448 EUR → unos pocos clientes tienen saldos enormes que suben el promedio.
- `age`: promedio ≈ 41 años, mediana = 39 años → distribución bastante equilibrada.
- `pdays`: promedio ≈ 40 días pero mediana = -1 → el 75% de los clientes nunca fue contactado antes (-1 significa "sin contacto previo").
"""

cat_col = ["job", "marital", "education","default", "housing","loan", "contact","month","poutcome", "y"]
for column in cat_col:
    print(data[column].value_counts(1))
    print("-" * 50)

"""**¿Qué nos dice esto?**

Aquí vemos qué tan frecuente es cada categoría dentro de las variables de texto. Algunos puntos destacados:
- **job**: Los trabajos más comunes son obrero industrial (blue-collar, 21.5%), gerencia (management, 20.9%) y técnico (technician, 16.8%).
- **marital**: La mayoría está casado (60.2%).
- **default**: Casi nadie tiene crédito en mora (solo 1.8%), por lo que esta variable no va a ser muy útil para distinguir clientes.
- **poutcome**: El 81.7% tiene resultado "desconocido" porque es la primera vez que son contactados en campaña.
"""

df_yes = df[df['y'] == 'yes']
cuartiles = df_yes['age'].describe()[['min', '25%', '50%', '75%', 'max']].to_frame(name='edad')
cuartiles

df.groupby('y')['age'].describe()

"""**¿Qué nos dice esto?**

Comparamos las edades entre los clientes que SÍ suscribieron vs. los que NO:
- Ambos grupos tienen edades similares (mediana ~38-39 años).
- Los clientes que suscribieron tienen una distribución de edades un poco más amplia (desviación estándar mayor), lo que sugiere que hay más suscriptores tanto en edades jóvenes como en edades avanzadas.
- La edad por sí sola no es un factor decisivo.

---
## 3a. Análisis Univariado

En esta sección miramos **cada variable por separado** para entender cómo están distribuidos los datos antes de relacionarlos con el resultado.

Usamos dos tipos de gráficos:
- **Histograma**: muestra cuántos clientes hay en cada rango de valores. Si la barra más alta está a la izquierda y va bajando hacia la derecha, hay pocos clientes con valores muy altos (sesgo a la derecha).
- **Boxplot (diagrama de caja)**: muestra el rango central de los datos. La caja contiene al 50% del medio de los clientes. La línea roja dentro de la caja es la mediana. Los círculos fuera de los "bigotes" son valores atípicos (outliers).

### Variables Numéricas

#### Tabla resumen: media, mediana y valores atípicos
"""

num_cols = ['age', 'balance', 'duration', 'campaign', 'pdays', 'previous', 'day']

stats = data[num_cols].agg(['mean', 'median', 'std', 'min', 'max']).T
stats.columns = ['Media (promedio)', 'Mediana (valor del medio)', 'Desv. Estándar', 'Mínimo', 'Máximo']

outlier_pct = []
for col in num_cols:
    Q1 = data[col].quantile(0.25)
    Q3 = data[col].quantile(0.75)
    IQR = Q3 - Q1
    n_outliers = ((data[col] < Q1 - 1.5 * IQR) | (data[col] > Q3 + 1.5 * IQR)).sum()
    outlier_pct.append(round(n_outliers / len(data) * 100, 2))

stats['% Valores atípicos'] = outlier_pct
stats = stats.round(2)

stats.style.background_gradient(cmap='Blues', subset=['Media (promedio)', 'Mediana (valor del medio)']) \
           .background_gradient(cmap='Reds', subset=['% Valores atípicos']) \
           .format(precision=2)

"""**Cómo leer esta tabla:**

- **Media vs. Mediana**: si la media es mucho más grande que la mediana, hay clientes con valores muy altos que "jalan" el promedio. Por ejemplo en `balance`, la media es 1,362 EUR pero la mediana es 448 EUR — la mayoría de los clientes tiene mucho menos que el promedio.
- **Desv. Estándar**: qué tan dispersos están los datos. Una desviación alta (como en `balance` = 3,044) significa que los saldos varían muchísimo entre clientes.
- **% Valores atípicos**: qué porcentaje de clientes tiene valores muy fuera de lo común. Un 9% en `campaign` significa que 1 de cada 11 clientes fue contactado una cantidad exagerada de veces.
"""

num_cols = ['age', 'balance', 'duration', 'campaign', 'pdays', 'previous', 'day']

fig, axes = plt.subplots(len(num_cols), 2, figsize=(14, 4 * len(num_cols)))
fig.suptitle('Distribución de Variables Numéricas', fontsize=16, fontweight='bold', y=1.01)

for i, col in enumerate(num_cols):
    media   = data[col].mean()
    mediana = data[col].median()

    axes[i, 0].hist(data[col], bins=40, color='steelblue', edgecolor='white', alpha=0.85)
    axes[i, 0].set_xlim(
    data[col].quantile(0.01),
    data[col].quantile(0.99)
)
    axes[i, 0].axvline(media,   color='red',    linestyle='--', linewidth=1.5, label=f'Media: {media:.1f}')
    axes[i, 0].axvline(mediana, color='orange', linestyle='-',  linewidth=1.5, label=f'Mediana: {mediana:.1f}')
    axes[i, 0].set_title(f'Histograma — {col}')
    axes[i, 0].set_xlabel(col)
    axes[i, 0].set_ylabel('Cantidad de clientes')
    axes[i, 0].grid(axis='y', alpha=0.4)
    axes[i, 0].legend(fontsize=9)

    axes[i, 1].boxplot(data[col], vert=False, patch_artist=True,
                       boxprops=dict(facecolor='steelblue', alpha=0.7),
                       medianprops=dict(color='red', linewidth=2))
    axes[i, 1].set_title(f'Boxplot — {col}  |  Media: {media:.1f}  |  Mediana: {mediana:.1f}')
    axes[i, 1].set_xlabel(col)
    axes[i, 1].grid(axis='x', alpha=0.4)
    axes[i, 1].set_xlim(
    data[col].quantile(0.01),
    data[col].quantile(0.99)
)

plt.tight_layout()
plt.show()

"""**¿Qué vemos en los gráficos?**

- **age (edad)**: La mayoría de los clientes tiene entre 30 y 50 años. La media (41 años) y la mediana (39 años) están muy cerca, lo que indica que la distribución es bastante equilibrada. Los círculos en el boxplot son clientes muy mayores (más de 70 años).

- **balance (saldo en cuenta)**: La barra del histograma está muy cargada a la izquierda — la mayoría tiene saldos bajos. La línea roja (media = 1,362 EUR) está muy a la derecha de la naranja (mediana = 448 EUR), confirmando que unos pocos clientes con saldos enormes distorsionan el promedio. También hay saldos negativos (clientes con deudas).

- **duration (duración de la llamada en segundos)**: La mayoría de las llamadas son cortas (menos de 500 segundos). Hay algunas muy largas que son outliers. La media (258 s) es mayor que la mediana (180 s) por esas llamadas largas.

- **campaign (cantidad de llamadas en esta campaña)**: Casi todos los clientes fueron contactados entre 1 y 3 veces. Los círculos del boxplot llegan hasta 63 — hay clientes que recibieron muchas más llamadas de lo normal.

- **pdays (días desde el último contacto previo)**: La gran mayoría tiene -1 (nunca fueron contactados antes). Por eso la mediana es -1 aunque la media sea 40 — la media está inflada por los pocos que sí tenían historial.

- **previous (contactos en campañas anteriores)**: Muy parecido a pdays. La mayoría tiene 0 contactos previos.

- **day (día del mes del contacto)**: Los clientes fueron contactados de forma bastante uniforme a lo largo del mes. No se ve un patrón claro por día.

Nota: Para facilitar la interpretación visual, los histogramas y boxplots se muestran con el eje X limitado entre los percentiles 1 y 99. Esta decisión mejora la visualización de la distribución principal sin modificar los datos analizados

### Variables Categóricas

#### Tabla de frecuencias — cuántos clientes hay en cada categoría
"""

cat_cols = ['job', 'marital', 'education', 'default', 'housing', 'loan',
            'contact', 'month', 'poutcome', 'y']

for col in cat_cols:
    freq = pd.DataFrame({
        'Categoría'  : data[col].value_counts().index,
        'Cantidad'   : data[col].value_counts().values,
        '% del total': (data[col].value_counts(normalize=True) * 100).round(2).values
    })
    print(f"\n{'='*45}")
    print(f"  {col.upper()}")
    print(f"{'='*45}")
    print(freq.to_string(index=False))

cat_cols = ['job', 'marital', 'education', 'default', 'housing', 'loan',
            'contact', 'month', 'poutcome', 'y']

fig, axes = plt.subplots(5, 2, figsize=(16, 22))
fig.suptitle('Distribución de Variables Categóricas', fontsize=16, fontweight='bold')
axes = axes.flatten()
colors = sns.color_palette('Set2', 12)

for i, col in enumerate(cat_cols):
    counts = data[col].value_counts()
    pcts   = data[col].value_counts(normalize=True) * 100
    bars = axes[i].bar(counts.index, pcts.values,
                       color=colors[:len(counts)], edgecolor='white', linewidth=0.8)
    axes[i].set_title(f'{col}', fontsize=13, fontweight='bold')
    axes[i].set_ylabel('% de clientes')
    axes[i].set_ylim(0, pcts.max() * 1.2)
    axes[i].tick_params(axis='x', rotation=30)
    axes[i].grid(axis='y', alpha=0.4)
    for bar, pct in zip(bars, pcts.values):
        axes[i].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.5,
                     f'{pct:.1f}%', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()

"""**¿Qué vemos en los gráficos?**

- **job**: Los trabajos más frecuentes son obreros industriales (blue-collar, 21.5%), gerencia (management, 20.9%) y técnicos (technician, 16.8%). Hay muy pocos clientes con trabajo desconocido (unknown, 0.6%).

- **marital**: La mayoría de los clientes está casado (60.2%). Los solteros son el 28.3% y los divorciados el 11.5%.

- **education**: Más de la mitad tiene educación secundaria (51.3%). El 29.4% tiene educación terciaria (universitaria). Solo el 4.1% tiene educación desconocida.

- **default**: Casi todos los clientes (98.2%) no tienen crédito en mora. Como casi todos caen en "no", esta variable tiene poca utilidad para diferenciar clientes.

- **housing**: Poco más de la mitad tiene hipoteca (55.6% sí vs. 44.4% no).

- **loan**: La gran mayoría no tiene préstamo personal (84%). Solo 1 de cada 6 clientes tiene préstamo.

- **contact**: El 64.8% fue contactado por celular. El 28.8% tiene tipo de contacto desconocido — no sabemos cómo los llamaron.

- **month**: Mayo concentra casi el 30% de todos los contactos. Los meses con menos llamadas son diciembre, marzo y septiembre.

- **poutcome**: El 81.7% tiene resultado "desconocido" porque es la primera vez que participan en una campaña. Solo el 3.3% tuvo éxito en una campaña anterior.

- **y (resultado final)**: Confirmamos el desbalance — 88.3% no suscribió y 11.7% sí. Hay casi 8 veces más "no" que "yes".

---
## 3b. Análisis Bivariado

Ahora miramos la relación entre **cada variable y el resultado** (`y`). La pregunta que queremos responder es: *¿esta variable ayuda a distinguir a los clientes que suscriben de los que no?*

### Variables Numéricas vs. Resultado (`y`)

Usamos boxplots comparando los dos grupos: clientes que dijeron **No** (rojo) vs. clientes que dijeron **Sí** (verde).

Si las cajas están en alturas muy diferentes, esa variable es útil para distinguir entre los dos grupos. Si las cajas se superponen mucho, esa variable no diferencia bien.
"""

num_cols = ['age', 'balance', 'duration', 'campaign', 'pdays', 'previous', 'day']

fig, axes = plt.subplots(4, 2, figsize=(14, 20))
fig.suptitle('¿Cómo varía cada variable según si el cliente suscribió o no?', fontsize=14, fontweight='bold')
axes = axes.flatten()

for i, col in enumerate(num_cols):
    groups = [data[data['y'] == 'no'][col], data[data['y'] == 'yes'][col]]
    bp = axes[i].boxplot(groups, labels=['No suscribió', 'Sí suscribió'],
                         patch_artist=True, vert=True, showfliers=False,
                         medianprops=dict(color='black', linewidth=2))
    bp['boxes'][0].set_facecolor('#e74c3c')
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor('#2ecc71')
    bp['boxes'][1].set_alpha(0.7)
    axes[i].set_title(f'{col}', fontsize=12)
    axes[i].set_ylabel(col)
    axes[i].grid(axis='y', alpha=0.4)
if col in ['balance', 'duration', 'campaign']:
    axes[i].set_ylim(
        data[col].quantile(0.01),
        data[col].quantile(0.99)
    )

axes[-1].set_visible(False)
plt.tight_layout()
plt.show()

"""**¿Qué vemos en los gráficos?**

- **age (edad)**: Las cajas están casi a la misma altura para ambos grupos. La edad por sí sola no diferencia mucho a los que suscriben de los que no.

- **balance (saldo)**: Los clientes que sí suscribieron tienen la caja verde un poco más alta — sus saldos son levemente mayores. No es una diferencia enorme, pero existe.

- **duration (duración de la llamada)**: ⭐ **Esta es la variable más importante.** La caja verde (sí suscribió) está claramente más alta que la roja. Los clientes que suscribieron tuvieron llamadas mucho más largas en promedio (mediana ~500 segundos) que los que no suscribieron (mediana ~180 segundos).

- **campaign (cantidad de llamadas)**: Los clientes que NO suscribieron recibieron más llamadas en promedio. Llamar muchas veces al mismo cliente no ayuda — puede generar rechazo.

- **pdays y previous**: Los clientes con contacto previo (valores distintos de -1 y 0) tienden a suscribir más. Tener historia con el cliente es una ventaja.

- **day (día del mes)**: Las cajas son prácticamente idénticas para ambos grupos. El día del mes no tiene relación con si el cliente suscribe o no.

### Variables Categóricas vs. Resultado (`y`)

Aquí calculamos la **tasa de suscripción** por categoría: de cada 100 clientes de ese grupo, ¿cuántos dijeron que sí?

La línea azul punteada es el **promedio global (11.7%)**. Las barras por encima de esa línea son grupos con mayor probabilidad de suscribir.
"""

cat_cols_biv = ['job', 'marital', 'education', 'default',
                'housing', 'loan', 'contact', 'month', 'poutcome']

fig, axes = plt.subplots(5, 2, figsize=(16, 26))
fig.suptitle('¿Qué porcentaje de cada grupo suscribió el depósito?', fontsize=14, fontweight='bold')
axes = axes.flatten()

for i, col in enumerate(cat_cols_biv):
    rate = (data.groupby(col)['y']
               .apply(lambda x: (x == 'yes').mean() * 100)
               .sort_values(ascending=False))
    bars = axes[i].bar(rate.index, rate.values,
                       color=sns.color_palette('RdYlGn', len(rate)), edgecolor='white')
    axes[i].axhline(y=data['y'].eq('yes').mean() * 100,
                    color='navy', linestyle='--', linewidth=1.5, label='Promedio global (11.7%)')
    axes[i].set_title(f'% suscripción por {col}', fontsize=12, fontweight='bold')
    axes[i].set_ylabel('% que suscribió')
    axes[i].tick_params(axis='x', rotation=35)
    axes[i].grid(axis='y', alpha=0.4)
    axes[i].legend(fontsize=8)
    for bar, val in zip(bars, rate.values):
        axes[i].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.3,
                     f'{val:.1f}%', ha='center', va='bottom', fontsize=8.5)

axes[-1].set_visible(False)
plt.tight_layout()
plt.show()

"""**¿Qué vemos en los gráficos?**

- **job (trabajo)**: Los **estudiantes (31.4%)** y **jubilados (25.2%)** son los grupos con mayor tasa de suscripción — casi el triple del promedio. Los obreros industriales (blue-collar) y empresarios tienen las tasas más bajas (alrededor del 7%).

- **marital (estado civil)**: Los **solteros** suscriben un poco más (14.4%) que los casados (10.7%) o divorciados (10.1%). La diferencia no es enorme pero existe.

- **education (educación)**: Los clientes con **educación universitaria (terciaria)** suscriben más (15%). Los de educación primaria tienen la tasa más baja (~9%).

- **default (mora)**: Los clientes **sin deudas en mora** suscriben más (11.9%) vs. los que sí tienen (6.9%). Tiene sentido: un cliente con problemas financieros es menos probable que quiera invertir.

- **housing (hipoteca)**: Los clientes **sin hipoteca** suscriben más del doble (16.6%) que los que tienen hipoteca (7.6%). Con una hipoteca activa, es más difícil comprometer dinero adicional.

- **loan (préstamo personal)**: Igual patrón que hipoteca — sin préstamo: 12.6%, con préstamo: 7.5%.

- **contact (tipo de contacto)**: El **celular** tiene la tasa más alta (14.8%). El teléfono fijo tiene la más baja (5.2%).

- **month (mes)**: ⭐ Los meses de **marzo, septiembre, octubre y diciembre** tienen tasas altísimas (más del 40% en algunos casos), aunque en esos meses se hicieron pocas llamadas. Mayo tiene muchísimas llamadas pero solo un 6% de conversión — se contactaron muchos clientes poco propensos.

- **poutcome (resultado de campaña anterior)**: ⭐ **El predictor más poderoso de las variables categóricas.** Si el cliente ya había tenido éxito en una campaña anterior, el **64.7% vuelve a suscribir**. Priorizar a estos clientes sería muy eficiente.

### Correlación entre variables numéricas

Esta matriz muestra qué tan relacionadas están las variables numéricas entre sí. Los valores van de -1 (relación inversa perfecta) a +1 (relación directa perfecta). Valores cercanos a 0 significan poca o ninguna relación.
"""

num_data = data[['age', 'balance', 'duration', 'campaign', 'pdays', 'previous', 'day']].copy()

plt.figure(figsize=(9, 7))
corr_matrix = num_data.corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            mask=mask, center=0, square=True, linewidths=0.5,
            cbar_kws={'shrink': 0.8})
plt.title('¿Cuánto se relacionan las variables numéricas entre sí?', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.show()

"""**¿Qué vemos?**

La mayoría de los valores están cerca de 0, lo que significa que las variables numéricas no están muy relacionadas entre sí. Eso es bueno para el modelo.

La correlación más alta es entre `pdays` y `previous` (0.45): tiene sentido porque ambas miden el historial de contacto previo — si alguien fue contactado muchas veces antes, también tendrá más días registrados desde el último contacto.

### Comparación entre variables categóricas entre sí

En este apartado analizamos cómo se relacionan los atributos categóricos de los clientes entre sí para entender mejor los perfiles sociodemográficos y financieros:
- **Ocupación vs. Nivel Educativo**: ¿ciertos trabajos concentran niveles específicos de estudio?
- **Estado Civil vs. Crédito Hipotecario**: ¿los clientes casados tienen mayor tendencia a tener hipoteca?
- **Hipoteca vs. Préstamo Personal**: ¿quiénes tienen hipoteca suelen endeudarse más con préstamos de consumo?
- **Resultado Previo vs. Canal de Contacto**: ¿cómo se contactó a los clientes según el resultado de campañas anteriores?
"""

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Comparación entre variables categóricas clave', fontsize=14, fontweight='bold')

# 1. Nivel educativo según ocupación (job vs education)
df_job_edu = pd.crosstab(data['job'], data['education'], normalize='index') * 100
df_job_edu.plot(kind='bar', stacked=True, ax=axes[0, 0], colormap='Blues', edgecolor='white', alpha=0.9)
axes[0, 0].set_title('Nivel educativo según ocupación (%)', fontsize=12, fontweight='bold')
axes[0, 0].set_ylabel('Porcentaje (%)')
axes[0, 0].set_xlabel('Trabajo (job)')
axes[0, 0].tick_params(axis='x', rotation=40)
axes[0, 0].legend(title='Educación', bbox_to_anchor=(1.02, 1), loc='upper left')
axes[0, 0].grid(axis='y', alpha=0.3)

# 2. Crédito hipotecario según estado civil (marital vs housing)
df_mar_house = pd.crosstab(data['marital'], data['housing'], normalize='index') * 100
df_mar_house.plot(kind='bar', stacked=True, ax=axes[0, 1], color=['#2b5c8f', '#e74c3c'], edgecolor='white', alpha=0.85)
axes[0, 1].set_title('Crédito hipotecario según estado civil (%)', fontsize=12, fontweight='bold')
axes[0, 1].set_ylabel('Porcentaje (%)')
axes[0, 1].set_xlabel('Estado civil (marital)')
axes[0, 1].tick_params(axis='x', rotation=0)
axes[0, 1].legend(title='¿Tiene hipoteca?', bbox_to_anchor=(1.02, 1), loc='upper left')
axes[0, 1].grid(axis='y', alpha=0.3)

# 3. Préstamo personal según tenencia de hipoteca (housing vs loan)
df_house_loan = pd.crosstab(data['housing'], data['loan'], normalize='index') * 100
df_house_loan.plot(kind='bar', stacked=True, ax=axes[1, 0], color=['#3498db', '#9b59b6'], edgecolor='white', alpha=0.85)
axes[1, 0].set_title('Préstamo personal según hipoteca (%)', fontsize=12, fontweight='bold')
axes[1, 0].set_ylabel('Porcentaje (%)')
axes[1, 0].set_xlabel('¿Tiene hipoteca? (housing)')
axes[1, 0].tick_params(axis='x', rotation=0)
axes[1, 0].legend(title='¿Tiene préstamo?', bbox_to_anchor=(1.02, 1), loc='upper left')
axes[1, 0].grid(axis='y', alpha=0.3)

# 4. Canal de contacto según resultado de campaña previa (poutcome vs contact)
df_pout_cont = pd.crosstab(data['poutcome'], data['contact'], normalize='index') * 100
df_pout_cont.plot(kind='bar', stacked=True, ax=axes[1, 1], colormap='crest', edgecolor='white', alpha=0.85)
axes[1, 1].set_title('Canal de contacto según resultado previo (%)', fontsize=12, fontweight='bold')
axes[1, 1].set_ylabel('Porcentaje (%)')
axes[1, 1].set_xlabel('Resultado campaña previa (poutcome)')
axes[1, 1].tick_params(axis='x', rotation=0)
axes[1, 1].legend(title='Tipo de contacto', bbox_to_anchor=(1.02, 1), loc='upper left')
axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

"""**¿Qué nos dicen estos cruces categóricos?**

- **Ocupación vs. Educación**: Existe una clara segmentación. Los cargos de gestión (`management`) tienen una alta concentración de educación terciaria/universitaria (>70%), mientras que los obreros (`blue-collar`) concentran educación secundaria y primaria.
- **Estado Civil vs. Hipoteca**: Los clientes casados (`married`) presentan una mayor proporción de crédito hipotecario que los solteros (`single`), quienes en su mayoría no tienen hipoteca activa.
- **Hipoteca vs. Préstamo personal**: Los clientes que ya tienen hipoteca tienen una ligera mayor propensión a tener también un préstamo personal en comparación con los que no tienen hipoteca.
- **Resultado previo vs. Contacto**: Para los clientes con éxito previo (`success`), el medio de contacto predominante y efectivo es el teléfono celular, con una presencia mínima de canales desconocidos.

### Matriz de Asociación entre Variables Categóricas (V de Cramér)

Para medir qué tan asociadas están las variables categóricas entre sí de forma global (análogo a la correlación en variables numéricas), calculamos la **V de Cramér**.
Los valores van de **0** (sin asociación) a **1** (asociación perfecta).
"""

from scipy.stats import chi2_contingency

def cramers_v(x, y):
    confusion_matrix = pd.crosstab(x, y)
    chi2 = chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum().sum()
    phi2 = chi2 / n
    r, k = confusion_matrix.shape
    phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
    rcorr = r - ((r-1)**2)/(n-1)
    kcorr = k - ((k-1)**2)/(n-1)
    denom = min((kcorr-1), (rcorr-1))
    return np.nan if denom == 0 else np.sqrt(phi2corr / denom)

cat_cols_all = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
matrix_cramer = pd.DataFrame(index=cat_cols_all, columns=cat_cols_all, dtype=float)

for col1 in cat_cols_all:
    for col2 in cat_cols_all:
        matrix_cramer.loc[col1, col2] = cramers_v(data[col1], data[col2])

plt.figure(figsize=(9, 7))
mask_cramer = np.triu(np.ones_like(matrix_cramer, dtype=bool))
sns.heatmap(matrix_cramer, annot=True, fmt='.2f', cmap='YlGnBu',
            mask=mask_cramer, square=True, linewidths=0.5, cbar_kws={'shrink': 0.8})
plt.title('Asociación entre variables categóricas (V de Cramér)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.show()

"""**¿Qué vemos en la matriz de Cramér?**

- Las asociaciones más fuertes se observan entre:
  - `job` y `education` (0.46): fuerte correspondencia entre nivel educativo y tipo de empleo.
  - `contact` y `month` (0.51): los canales de comunicación variaron según la época o fase de la campaña.
  - `housing` y `month` (0.50): estacionalidad en la oferta o perfil de clientes contactados con hipoteca.
- El resto de combinaciones muestra asociaciones bajas o moderadas, lo cual es deseable porque reduce el riesgo de redundancia o multicolinealidad entre predictores categóricos.

---
## Resumen de lo que aprendimos en el EDA

| Variable | Qué encontramos | Qué significa para el banco |
|----------|----------------|---------------------------|
| `duration` | Llamadas más largas → más suscripciones | Hay que lograr que el cliente se enganche en la conversación |
| `poutcome` | Éxito previo = 64.7% de conversión | Llamar primero a clientes que ya suscribieron antes |
| `month` | Mar/Sep/Oct/Dic tienen tasas altísimas | Concentrar la campaña en esos meses |
| `job` | Estudiantes y jubilados suscriben más | Apuntar a esos segmentos con mensajes personalizados |
| `housing` y `loan` | Sin deudas = más propenso a suscribir | Filtrar a clientes sin compromisos financieros activos |
| `campaign` | Más llamadas = menos suscripciones | No insistir demasiado; priorizar calidad sobre cantidad |
| `contact` | Celular supera al teléfono fijo | Usar celular como canal preferido |
| `balance` | Mayor saldo = leve mayor propensión | El saldo puede ser un criterio de selección de clientes |

> **Nota importante**: el dataset está desbalanceado (88.3% / 11.7%). Cuando construyamos el modelo de Machine Learning, vamos a necesitar técnicas especiales para que el modelo aprenda bien a identificar los clientes que SÍ suscriben.
"""



# Commented out IPython magic to ensure Python compatibility.
# %%writefile app.py
# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# 
# # 1. Configuración de la página
# st.set_page_config(
#     page_title="Dashboard Bank Marketing - EDA",
#     layout="wide"
# )
# 
# st.title("Análisis EDA: Factores Determinantes de Suscripción al Plazo Fijo")
# st.write("Proyecto Integrador UTEC - Grupo 8")
# st.markdown("---")
# 
# RUTA_DRIVE = '/content/drive/MyDrive/UTEC - TEC /bank-full.csv'
# 
# @st.cache_data
# def cargar_datos():
#     return pd.read_csv(RUTA_DRIVE, sep=';')
# 
# try:
#     df_raw = cargar_datos()
# 
#     # PALETA MONOCROMÁTICA
#     COLOR_NO = '#D1D5DB'   # Gris claro para "no"
#     COLOR_SI = '#374151'   # Gris oscuro para "yes"
# 
#     # BARRA LATERAL: FILTROS GLOBALES
#     st.sidebar.header("Filtros de Exploración")
# 
#     trabajos_disponibles = sorted(df_raw['job'].unique().tolist())
#     trabajos_sel = st.sidebar.multiselect("Ocupación / Trabajo:", trabajos_disponibles, default=trabajos_disponibles)
# 
#     marital_disponibles = sorted(df_raw['marital'].unique().tolist())
#     marital_sel = st.sidebar.multiselect("Estado Civil:", marital_disponibles, default=marital_disponibles)
# 
#     educacion_disponibles = sorted(df_raw['education'].unique().tolist())
#     educacion_sel = st.sidebar.multiselect("Nivel Educativo:", educacion_disponibles, default=educacion_disponibles)
# 
#     edad_min, edad_max = int(df_raw['age'].min()), int(df_raw['age'].max())
#     rango_edad = st.sidebar.slider("Rango de Edad:", edad_min, edad_max, (edad_min, edad_max))
# 
#     df = df_raw[
#         (df_raw['job'].isin(trabajos_sel)) &
#         (df_raw['marital'].isin(marital_sel)) &
#         (df_raw['education'].isin(educacion_sel)) &
#         (df_raw['age'].between(rango_edad[0], rango_edad[1]))
#     ]
# 
#     # KPIs PRINCIPALES
#     total_clientes = len(df)
#     total_yes = len(df[df['y'] == 'yes'])
#     tasa_conversion_global = (total_yes / total_clientes * 100) if total_clientes > 0 else 0
#     balance_promedio = df['balance'].mean() if total_clientes > 0 else 0
# 
#     def crear_kpi_card(titulo, valor):
#         return f"""
#         <div style="
#             background-color: #F8FAFC;
#             border: 1px solid #E2E8F0;
#             border-top: 4px solid #374151;
#             border-radius: 8px;
#             padding: 16px 12px;
#             text-align: center;
#             box-shadow: 0 2px 4px rgba(0,0,0,0.04);
#             margin-bottom: 10px;
#         ">
#             <p style="margin: 0; font-size: 14px; font-weight: 600; color: #475569;">{titulo}</p>
#             <h2 style="margin: 6px 0 0 0; font-size: 32px; font-weight: 700; color: #0F172A;">{valor}</h2>
#         </div>
#         """
# 
#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         st.markdown(crear_kpi_card("Clientes filtrados", f"{total_clientes:,}"), unsafe_allow_html=True)
#     with c2:
#         st.markdown(crear_kpi_card("Suscripciones ('yes')", f"{total_yes:,}"), unsafe_allow_html=True)
#     with c3:
#         st.markdown(crear_kpi_card("Tasa de conversión global", f"{tasa_conversion_global:.2f}%"), unsafe_allow_html=True)
#     with c4:
#         st.markdown(crear_kpi_card("Balance promedio", f"€{balance_promedio:,.0f}"), unsafe_allow_html=True)
# 
#     st.markdown("---")
# 
#     # SELECCIÓN Y CLASIFICACIÓN DE VARIABLES
#     st.header("Suscripción por variable")
# 
#     tipo_variable = st.radio(
#         "Seleccione Clasificación de Variable:",
#         ["Variables Cualitativas (Categóricas)", "Variables Cuantitativas (Numéricas)"],
#         horizontal=True
#     )
# 
#     # ---------------------------------------------------------
#     # RAMA 1: CUALITATIVAS
#     # ---------------------------------------------------------
#     if tipo_variable == "Variables Cualitativas (Categóricas)":
#         dict_cualitativas = {
#             "Ocupación (job)": "job",
#             "Estado Civil (marital)": "marital",
#             "Nivel Educativo (education)": "education",
#             "Crédito en Default (default)": "default",
#             "Crédito Hipotecario (housing)": "housing",
#             "Crédito Personal (loan)": "loan",
#             "Medio de Contacto (contact)": "contact",
#             "Mes de Contacto (month)": "month",
#             "Resultado Campaña Previa (poutcome)": "poutcome"
#         }
#         var_label = st.selectbox("Elegí la variable categórica:", list(dict_cualitativas.keys()))
#         var_col = dict_cualitativas[var_label]
# 
#         if not df.empty:
#             df_counts = df.groupby([var_col, 'y']).size().unstack(fill_value=0).reset_index()
#             if 'yes' not in df_counts.columns: df_counts['yes'] = 0
#             if 'no' not in df_counts.columns: df_counts['no'] = 0
# 
#             df_counts['Total'] = df_counts['yes'] + df_counts['no']
#             df_counts['Tasa_Exito_%'] = (df_counts['yes'] / df_counts['Total'] * 100).round(1)
#             df_counts['Texto_Porcentaje'] = df_counts['Tasa_Exito_%'].astype(str) + '%'
# 
#             col1, col2 = st.columns(2)
# 
#             with col1:
#                 st.subheader("Frecuencia absoluta")
#                 df_melt = df_counts.melt(id_vars=[var_col], value_vars=['no', 'yes'], var_name='¿Suscribió?', value_name='Número de clientes')
# 
#                 fig_abs = px.bar(
#                     df_melt,
#                     x=var_col,
#                     y='Número de clientes',
#                     color='¿Suscribió?',
#                     barmode='group',
#                     text_auto=',d',
#                     template='plotly_white',
#                     color_discrete_map={'yes': COLOR_SI, 'no': COLOR_NO},
#                     labels={var_col: var_col, 'Número de clientes': 'Número de clientes'}
#                 )
#                 fig_abs.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
#                 fig_abs.update_layout(
#                     margin=dict(l=10, r=10, t=30, b=20),
#                     xaxis=dict(tickangle=-35),
#                     legend_title_text='¿Suscribió?'
#                 )
#                 st.plotly_chart(fig_abs, use_container_width=True)
# 
#             with col2:
#                 st.subheader("Porcentaje (tasa de conversión)")
#                 df_sorted = df_counts.sort_values(by='Tasa_Exito_%', ascending=False)
# 
#                 fig_pct = px.bar(
#                     df_sorted,
#                     x=var_col,
#                     y='Tasa_Exito_%',
#                     color='Tasa_Exito_%',
#                     text='Texto_Porcentaje',
#                     color_continuous_scale=['#D1D5DB', '#6B7280', '#1F2937'],
#                     template='plotly_white',
#                     labels={var_col: var_col, 'Tasa_Exito_%': '% que suscribió'}
#                 )
#                 fig_pct.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
#                 fig_pct.update_layout(
#                     margin=dict(l=10, r=10, t=30, b=20),
#                     xaxis=dict(tickangle=-35),
#                     coloraxis_showscale=True,
#                     yaxis=dict(range=[0, max(df_sorted['Tasa_Exito_%'].max() * 1.2, 10)])
#                 )
#                 st.plotly_chart(fig_pct, use_container_width=True)
# 
#             # BLOQUE DE CONCLUSIONES AUTOMÁTICAS
#             top_conv = df_counts.sort_values(by='Tasa_Exito_%', ascending=False).iloc[0]
#             top_vol = df_counts.sort_values(by='Total', ascending=False).iloc[0]
#             diff_media = round(top_conv['Tasa_Exito_%'] - tasa_conversion_global, 1)
# 
#             st.markdown(f"""
#             <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 16px; border-radius: 6px; margin: 15px 0;">
#                 <h4 style="margin:0 0 8px 0; color: #15803D;">💡 Hallazgos Clave para {var_label}</h4>
#                 <ul style="margin: 0; padding-left: 20px; color: #166534; font-size: 15px;">
#                     <li><b>Mayor efectividad de conversión:</b> El segmento <b>{top_conv[var_col]}</b> alcanza una conversión del <b>{top_conv['Tasa_Exito_%']}%</b> ({'＋' if diff_media >= 0 else ''}{diff_media} puntos porcentuales respecto al promedio global de {tasa_conversion_global:.1f}%).</li>
#                     <li><b>Mayor concentración de volumen:</b> La mayor parte del público objetivo contactado corresponde a <b>{top_vol[var_col]}</b> con <b>{top_vol['Total']:,} clientes</b> (representando el {(top_vol['Total']/total_clientes*100):.1f}% de la muestra).</li>
#                     <li><b>Conclusión rápida:</b> Aunque {top_vol[var_col]} aporta volumen, enfocar esfuerzos comerciales en {top_conv[var_col]} incrementará significativamente el ROI de la campaña.</li>
#                 </ul>
#             </div>
#             """, unsafe_allow_html=True)
# 
#             st.subheader(f"Resumen Numérico EDA - {var_label}")
#             df_tabla = df_counts.sort_values(by='Tasa_Exito_%', ascending=False)[
#                 [var_col, 'yes', 'no', 'Total', 'Tasa_Exito_%']
#             ].rename(columns={'yes': 'Suscripciones (Sí)', 'no': 'No Suscritos (No)', 'Tasa_Exito_%': 'Tasa de Conversión (%)'})
#             st.dataframe(df_tabla, use_container_width=True)
# 
#     # ---------------------------------------------------------
#     # RAMA 2: CUANTITATIVAS
#     # ---------------------------------------------------------
#     else:
#         dict_cuantitativas = {
#             "Edad (age)": "age",
#             "Balance Anual en Euros (balance)": "balance",
#             "Duración del Contacto en Segundos (duration)": "duration",
#             "Contactos en esta Campaña (campaign)": "campaign",
#             "Días desde Campaña Previa (pdays)": "pdays",
#             "Contactos Previos (previous)": "previous"
#         }
#         var_label = st.selectbox("Elegí la variable numérica:", list(dict_cuantitativas.keys()))
#         var_col = dict_cuantitativas[var_label]
# 
#         if not df.empty:
#             df_num = df.copy()
# 
#             if var_col == 'age':
#                 bins = [-np.inf, 25, 35, 50, 60, np.inf]
#                 labels = ['<25 años', '25-35 años', '36-50 años', '51-60 años', '>60 años']
#             elif var_col == 'balance':
#                 bins = [-np.inf, 0, 500, 2000, np.inf]
#                 labels = ['Saldo < 0 €', '0 - 500 €', '500 - 2.000 €', '> 2.000 €']
#             elif var_col == 'duration':
#                 bins = [-np.inf, 120, 300, 600, np.inf]
#                 labels = ['<2 min', '2-5 min', '5-10 min', '>10 min']
#             elif var_col == 'campaign':
#                 bins = [-np.inf, 1, 2, 4, np.inf]
#                 labels = ['1 contacto', '2 contactos', '3-4 contactos', '5+ contactos']
#             elif var_col == 'pdays':
#                 bins = [-np.inf, -0.5, 90, 180, 360, np.inf]
#                 labels = ['Sin contacto (-1)', '0-90 días', '91-180 días', '181-360 días', '>360 días']
#             elif var_col == 'previous':
#                 bins = [-np.inf, 0, 1, 3, np.inf]
#                 labels = ['0 contactos', '1 contacto', '2-3 contactos', '4+ contactos']
# 
#             df_num['Rango'] = pd.cut(df_num[var_col], bins=bins, labels=labels, right=True)
# 
#             df_counts = df_num.groupby(['Rango', 'y'], observed=False).size().unstack(fill_value=0).reset_index()
#             if 'yes' not in df_counts.columns: df_counts['yes'] = 0
#             if 'no' not in df_counts.columns: df_counts['no'] = 0
# 
#             df_counts['Total'] = df_counts['yes'] + df_counts['no']
#             df_counts['Tasa_Exito_%'] = np.where(df_counts['Total'] > 0, (df_counts['yes'] / df_counts['Total'] * 100).round(1), 0)
#             df_counts['Texto_Porcentaje'] = df_counts['Tasa_Exito_%'].astype(str) + '%'
# 
#             col1, col2 = st.columns(2)
# 
#             with col1:
#                 st.subheader("Frecuencia absoluta")
#                 df_melt = df_counts.melt(id_vars=['Rango'], value_vars=['no', 'yes'], var_name='¿Suscribió?', value_name='Número de clientes')
# 
#                 fig_abs = px.bar(
#                     df_melt,
#                     x='Rango',
#                     y='Número de clientes',
#                     color='¿Suscribió?',
#                     barmode='group',
#                     text_auto=',d',
#                     template='plotly_white',
#                     color_discrete_map={'yes': COLOR_SI, 'no': COLOR_NO},
#                     labels={'Rango': var_label, 'Número de clientes': 'Número de clientes'}
#                 )
#                 fig_abs.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
#                 fig_abs.update_layout(
#                     margin=dict(l=10, r=10, t=30, b=20),
#                     xaxis=dict(tickangle=-25),
#                     legend_title_text='¿Suscribió?'
#                 )
#                 st.plotly_chart(fig_abs, use_container_width=True)
# 
#             with col2:
#                 st.subheader("Porcentaje (tasa de conversión)")
# 
#                 fig_pct = px.bar(
#                     df_counts,
#                     x='Rango',
#                     y='Tasa_Exito_%',
#                     color='Tasa_Exito_%',
#                     text='Texto_Porcentaje',
#                     color_continuous_scale=['#D1D5DB', '#6B7280', '#1F2937'],
#                     template='plotly_white',
#                     labels={'Rango': var_label, 'Tasa_Exito_%': '% que suscribió'}
#                 )
#                 fig_pct.update_traces(textposition='outside', textfont_size=11, textfont_color='black', cliponaxis=False)
#                 fig_pct.update_layout(
#                     margin=dict(l=10, r=10, t=30, b=20),
#                     xaxis=dict(tickangle=-25),
#                     coloraxis_showscale=True,
#                     yaxis=dict(range=[0, max(df_counts['Tasa_Exito_%'].max() * 1.2, 10)])
#                 )
#                 st.plotly_chart(fig_pct, use_container_width=True)
# 
#             # BLOQUE DE CONCLUSIONES AUTOMÁTICAS
#             top_conv = df_counts.sort_values(by='Tasa_Exito_%', ascending=False).iloc[0]
#             top_vol = df_counts.sort_values(by='Total', ascending=False).iloc[0]
#             diff_media = round(top_conv['Tasa_Exito_%'] - tasa_conversion_global, 1)
# 
#             st.markdown(f"""
#             <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; padding: 16px; border-radius: 6px; margin: 15px 0;">
#                 <h4 style="margin:0 0 8px 0; color: #15803D;">💡 Hallazgos Clave para {var_label}</h4>
#                 <ul style="margin: 0; padding-left: 20px; color: #166534; font-size: 15px;">
#                     <li><b>Rango con mayor conversión:</b> El rango <b>{top_conv['Rango']}</b> presenta la mayor tasa de aceptación con un <b>{top_conv['Tasa_Exito_%']}%</b> ({'＋' if diff_media >= 0 else ''}{diff_media}% comparado a la media global del {tasa_conversion_global:.1f}%).</li>
#                     <li><b>Volumen concentrado:</b> La mayor parte de los registros ({top_vol['Total']:,} personas, el {(top_vol['Total']/total_clientes*100):.1f}% del total) se ubica en el rango <b>{top_vol['Rango']}</b>.</li>
#                     <li><b>Lectura de negocio:</b> Existe una oportunidad clara al priorizar la gestión en el segmento <b>{top_conv['Rango']}</b>, que convierte sensiblemente por encima del promedio del banco.</li>
#                 </ul>
#             </div>
#             """, unsafe_allow_html=True)
# 
#             st.subheader(f"Resumen Numérico EDA - {var_label}")
#             df_tabla = df_counts[
#                 ['Rango', 'yes', 'no', 'Total', 'Tasa_Exito_%']
#             ].rename(columns={
#                 'Rango': f'Rango de {var_label}',
#                 'yes': 'Suscripciones (Sí)',
#                 'no': 'No Suscritos (No)',
#                 'Tasa_Exito_%': 'Tasa de Conversión (%)'
#             })
#             st.dataframe(df_tabla, use_container_width=True)
# 
# # ==========================================
#     # SECCIÓN ADICIONAL: ANÁLISIS MULTIVARIADO
#     # ==========================================
#     st.markdown("---")
#     st.header("Análisis Multivariado: Cruces Cualitativos")
#     st.caption("Evaluación de la tasa de suscripción combinando múltiples dimensiones.")
# 
#     # Variable aux para cálculo de tasa (%) en los cruces
#     df_temp = df.copy()
#     df_temp['target_num'] = (df_temp['y'] == 'yes').astype(int)
# 
#     # CRUCE 1: Ocupación vs Estado Civil
#     st.subheader("1. Tasa de Conversión (%) por Ocupación y Estado Civil")
#     df_cruce1 = df_temp.groupby(['job', 'marital'], observed=False)['target_num'].mean().reset_index()
#     df_cruce1['Tasa_%'] = (df_cruce1['target_num'] * 100).round(1)
# 
#     fig_m1 = px.bar(
#         df_cruce1,
#         x='job',
#         y='Tasa_%',
#         color='marital',
#         barmode='group',
#         text='Tasa_%',
#         color_discrete_sequence=['#252525', '#636363', '#969696', '#cccccc'],
#         template='plotly_white',
#         labels={'job': 'Ocupación', 'Tasa_%': 'Tasa de Conversión (%)', 'marital': 'Estado Civil'}
#     )
#     fig_m1.update_traces(textposition='outside', textfont_size=10)
#     fig_m1.update_layout(margin=dict(l=10, r=10, t=30, b=20), xaxis=dict(tickangle=-35))
#     st.plotly_chart(fig_m1, use_container_width=True)
# 
#     # CRUCE 2: Nivel Educativo vs Crédito Hipotecario
#     st.subheader("2. Tasa de Conversión (%) por Educación y Crédito Hipotecario")
#     df_cruce2 = df_temp.groupby(['education', 'housing'], observed=False)['target_num'].mean().reset_index()
#     df_cruce2['Tasa_%'] = (df_cruce2['target_num'] * 100).round(1)
# 
#     fig_m2 = px.bar(
#         df_cruce2,
#         x='education',
#         y='Tasa_%',
#         color='housing',
#         barmode='group',
#         text='Tasa_%',
#         color_discrete_sequence=['#252525', '#969696'],
#         template='plotly_white',
#         labels={'education': 'Nivel Educativo', 'Tasa_%': 'Tasa de Conversión (%)', 'housing': 'Tiene Hipoteca'}
#     )
#     fig_m2.update_traces(textposition='outside', textfont_size=10)
#     fig_m2.update_layout(margin=dict(l=10, r=10, t=30, b=20))
#     st.plotly_chart(fig_m2, use_container_width=True)
# 
#     # CRUCE 3: Canal de Contacto vs Resultado Campaña Previa
#     st.subheader("3. Tasa de Conversión (%) por Canal de Contacto y Resultado Previo")
#     df_cruce3 = df_temp.groupby(['contact', 'poutcome'], observed=False)['target_num'].mean().reset_index()
#     df_cruce3['Tasa_%'] = (df_cruce3['target_num'] * 100).round(1)
# 
#     fig_m3 = px.bar(
#         df_cruce3,
#         x='contact',
#         y='Tasa_%',
#         color='poutcome',
#         barmode='group',
#         text='Tasa_%',
#         color_discrete_sequence=['#252525', '#636363', '#969696', '#cccccc'],
#         template='plotly_white',
#         labels={'contact': 'Canal de Contacto', 'Tasa_%': 'Tasa de Conversión (%)', 'poutcome': 'Resultado Previo'}
#     )
#     fig_m3.update_traces(textposition='outside', textfont_size=10)
#     fig_m3.update_layout(margin=dict(l=10, r=10, t=30, b=20))
#     st.plotly_chart(fig_m3, use_container_width=True)
#     st.markdown("---")
#     st.subheader("Muestra de Datos Filtrados")
#     st.dataframe(df.head(10), use_container_width=True)
# 
# except Exception as e:
#     st.error(f"Error al cargar los datos: {e}")

""" import os
import subprocess
from pyngrok import ngrok

# 1. Limpiar procesos viejos
subprocess.run(["pkill", "-f", "ngrok"])
subprocess.run(["pkill", "-f", "streamlit"])

# 2. Configurar Token
NGROK_TOKEN = "3HF9CYpSYKcSv3whzvqDfOddgYR_5Shj3WcB1uMZewrKdYbHX"  # Pegá tu token acá adentro

ngrok.kill()
ngrok.set_auth_token(NGROK_TOKEN)

# 3. Lanzar Streamlit
os.system("streamlit run app.py --server.port 8501 &")

# 4. Conectar usando el dominio asignado a tu cuenta
DOMINIO_NGROK = "moonbeam-copper-underpaid.ngrok-free.dev"

try:
    public_url = ngrok.connect(8501, domain=DOMINIO_NGROK)
    print("\n--------------------------------------------------")
    print("Enlace a tu Dashboard de Streamlit:")
    print(public_url)
    print("--------------------------------------------------\n")
except Exception as e:
    print("\nError al conectar:", e)
  """
