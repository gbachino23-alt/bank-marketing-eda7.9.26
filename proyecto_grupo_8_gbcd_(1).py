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

    # PALETA DE COLORES
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
    # SECCIÓN ADICIONAL: ANÁLISIS MULTIVARIADO
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
    st.error(f"Error al cargar los datos: {e}")
