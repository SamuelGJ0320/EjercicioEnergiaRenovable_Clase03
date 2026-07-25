import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from groq import Groq

st.set_page_config(page_title="Dashboard Energía Renovable", layout="wide")

df = pd.read_csv("energia_renovable.csv")
df["Fecha_Entrada_Operacion"] = pd.to_datetime(df["Fecha_Entrada_Operacion"])

top_ops = df["Operador"].value_counts().reset_index()
top_ops.columns = ["Operador", "Cantidad"]
en_operacion = df[df["Estado_Actual"] == "Operación Comercial"].shape[0]
pct_operacion = en_operacion / df.shape[0] * 100
no_conectados = df[df["Conectado_SIN"] == False].shape[0]
proyectos_por_ano = df["Fecha_Entrada_Operacion"].dt.year.value_counts().sort_index().reset_index()
proyectos_por_ano.columns = ["Año", "Cantidad"]
max_ano = proyectos_por_ano.loc[proyectos_por_ano["Cantidad"].idxmax()]

st.title("Radiografía del Sector de Energía Renovable en Colombia")

st.markdown("""
Este dashboard explora el panorama de proyectos de energía renovable en Colombia,
analizando la distribución tecnológica, los actores del mercado, la eficiencia operativa
y la evolución del sector a través del tiempo.
""")

st.header("Panorama General")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Proyectos", df.shape[0])
col2.metric("Capacidad Total (MW)", f"{df['Capacidad_Instalada_MW'].sum():,.0f}")
col3.metric("Generación Diaria (MWh)", f"{df['Generacion_Diaria_MWh'].sum():,.0f}")
col4.metric("Inversión Total (M USD)", f"{df['Inversion_Inicial_MUSD'].sum():,.0f}")

st.sidebar.header("Configuración GROQ")
api_key = st.sidebar.text_input(
    "API Key",
    type="password",
    placeholder="gsk_...",
    help="Requerida para el Chatbot y el Extractor de Datos"
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Composición Tecnológica",
    "Actores del Mercado",
    "Madurez y Conectividad",
    "Evolución Temporal",
    "Estadístico (Seaborn)",
    "Clásico (Pyplot)",
    "Reportes",
    "Chatbot",
    "Extractor de Datos"
])

with tab1:
    st.subheader("¿Qué tecnologías dominan el sector?")

    col_a, col_b = st.columns(2)

    with col_a:
        tec_counts = df["Tecnologia"].value_counts().reset_index()
        tec_counts.columns = ["Tecnologia", "Cantidad"]
        tec_counts["Porcentaje"] = (tec_counts["Cantidad"] / tec_counts["Cantidad"].sum() * 100).round(1)
        fig_tec = px.pie(tec_counts, names="Tecnologia", values="Cantidad",
                         title="Proyectos por Tecnología",
                         hole=0.4)
        st.plotly_chart(fig_tec, use_container_width=True)

    with col_b:
        cap_tec = df.groupby("Tecnologia")["Capacidad_Instalada_MW"].sum().reset_index().sort_values("Capacidad_Instalada_MW", ascending=False)
        fig_cap = px.bar(cap_tec, x="Tecnologia", y="Capacidad_Instalada_MW",
                         title="Capacidad Instalada Total por Tecnología (MW)",
                         color="Tecnologia", text_auto=".0f")
        st.plotly_chart(fig_cap, use_container_width=True)

    st.markdown(f"""
    **Insight:** La tecnología más utilizada es **{tec_counts.iloc[0]['Tecnologia']}** con {tec_counts.iloc[0]['Cantidad']} proyectos ({tec_counts.iloc[0]['Porcentaje']}% del total),
    seguida de **{tec_counts.iloc[1]['Tecnologia']}** con {tec_counts.iloc[1]['Cantidad']} proyectos.
    """)

    st.subheader("Eficiencia vs Capacidad: ¿qué tecnología es más productiva?")
    fig_eff = px.scatter(df, x="Capacidad_Instalada_MW", y="Eficiencia_Planta_Pct",
                         color="Tecnologia", size="Generacion_Diaria_MWh",
                         hover_data=["ID_Proyecto", "Operador"],
                         title="Relación entre Capacidad Instalada y Eficiencia")
    st.plotly_chart(fig_eff, use_container_width=True)

    eff_tec = df.groupby("Tecnologia")["Eficiencia_Planta_Pct"].mean().reset_index().sort_values("Eficiencia_Planta_Pct", ascending=False)
    st.markdown(f"""
    **Insight:** La tecnología con mayor eficiencia promedio es **{eff_tec.iloc[0]['Tecnologia']}** ({eff_tec.iloc[0]['Eficiencia_Planta_Pct']:.1f}%),
    mientras que la de menor eficiencia es **{eff_tec.iloc[-1]['Tecnologia']}** ({eff_tec.iloc[-1]['Eficiencia_Planta_Pct']:.1f}%).
    """)

    fig_box = px.box(df, x="Tecnologia", y="Eficiencia_Planta_Pct",
                     title="Distribución de Eficiencia por Tecnología",
                     color="Tecnologia")
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    st.subheader("¿Quiénes invierten en energía renovable?")

    fig_ops = px.bar(top_ops, x="Operador", y="Cantidad",
                     title="Cantidad de Proyectos por Operador",
                     color="Cantidad", text_auto=True,
                     color_continuous_scale="Blues")
    st.plotly_chart(fig_ops, use_container_width=True)

    st.markdown(f"""
    **Insight:** El operador con más proyectos es **{top_ops.iloc[0]['Operador']}** ({top_ops.iloc[0]['Cantidad']} proyectos),
    seguido por **{top_ops.iloc[1]['Operador']}** ({top_ops.iloc[1]['Cantidad']}) y **{top_ops.iloc[2]['Operador']}** ({top_ops.iloc[2]['Cantidad']}).
    """)

    st.subheader("Inversión: ¿quién apuesta más fuerte?")
    inv_ops = df.groupby("Operador").agg(
        Inversion_Total=("Inversion_Inicial_MUSD", "sum"),
        Capacidad_Total=("Capacidad_Instalada_MW", "sum")
    ).reset_index().sort_values("Inversion_Total", ascending=False)

    fig_inv_op = px.bar(inv_ops.head(10), x="Operador", y="Inversion_Total",
                        title="Top 10 Operadores por Inversión Total (M USD)",
                        color="Inversion_Total", text_auto=".1f",
                        color_continuous_scale="Greens")
    st.plotly_chart(fig_inv_op, use_container_width=True)

    st.subheader("Relación Inversión vs Capacidad instalada")
    fig_inv = px.scatter(df, x="Capacidad_Instalada_MW", y="Inversion_Inicial_MUSD",
                         color="Operador", size="Generacion_Diaria_MWh",
                         hover_data=["Tecnologia", "ID_Proyecto"],
                         title="Cada punto es un proyecto: inversión vs capacidad")
    st.plotly_chart(fig_inv, use_container_width=True)

with tab3:
    st.subheader("¿En qué estado se encuentran los proyectos?")

    estado_counts = df["Estado_Actual"].value_counts().reset_index()
    estado_counts.columns = ["Estado", "Cantidad"]
    fig_est = px.bar(estado_counts, x="Estado", y="Cantidad",
                     title="Distribución por Estado Actual",
                     color="Cantidad", text_auto=True,
                     color_continuous_scale="Viridis")
    st.plotly_chart(fig_est, use_container_width=True)

    estado_tec = df.groupby(["Estado_Actual", "Tecnologia"]).size().reset_index(name="Cantidad")
    fig_est_tec = px.bar(estado_tec, x="Estado_Actual", y="Cantidad",
                         color="Tecnologia", title="Estado por Tecnología",
                         barmode="stack", text_auto=True)
    st.plotly_chart(fig_est_tec, use_container_width=True)

    st.markdown(f"""
    **Insight:** Solo **{en_operacion} proyectos ({pct_operacion:.1f}%)** están en operación comercial.
    El resto se encuentra en construcción, mantenimiento, pruebas o planeación, lo que refleja un sector en plena expansión.
    """)

    st.subheader("Conexión al Sistema Interconectado Nacional (SIN)")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        con_sin = df["Conectado_SIN"].value_counts().reset_index()
        con_sin.columns = ["Conectado_SIN", "Cantidad"]
        con_sin["Conectado_SIN"] = con_sin["Conectado_SIN"].map({True: "Conectado", False: "No conectado"})
        fig_con = px.pie(con_sin, names="Conectado_SIN", values="Cantidad",
                         title="Conexión al SIN", hole=0.4)
        st.plotly_chart(fig_con, use_container_width=True)

    with col_c2:
        sin_tec = df.groupby(["Tecnologia", "Conectado_SIN"]).size().reset_index(name="Cantidad")
        sin_tec["Conectado_SIN"] = sin_tec["Conectado_SIN"].map({True: "Conectado", False: "No conectado"})
        fig_sin_tec = px.bar(sin_tec, x="Tecnologia", y="Cantidad",
                             color="Conectado_SIN", title="Conexión al SIN por Tecnología",
                             barmode="group", text_auto=True)
        st.plotly_chart(fig_sin_tec, use_container_width=True)

    st.markdown(f"""
    **Insight:** **{no_conectados} proyectos ({no_conectados/df.shape[0]*100:.1f}%)** no están conectados al SIN,
    lo que puede limitar su capacidad de distribución energética a nivel nacional.
    """)

with tab4:
    st.subheader("¿Cómo ha evolucionado el sector en el tiempo?")

    fig_time = px.bar(proyectos_por_ano, x="Año", y="Cantidad",
                      title="Proyectos por Año de Entrada en Operación",
                      text_auto=True, color="Cantidad",
                      color_continuous_scale="Oranges")
    st.plotly_chart(fig_time, use_container_width=True)

    st.markdown(f"""
    **Insight:** El año con mayor cantidad de proyectos nuevos fue **{int(max_ano['Año'])}** con {int(max_ano['Cantidad'])} proyectos,
    lo que evidencia el momento de mayor dinamismo en el sector.
    """)

    evol_tec = df.groupby([df["Fecha_Entrada_Operacion"].dt.year, "Tecnologia"]).size().reset_index(name="Cantidad")
    evol_tec.columns = ["Año", "Tecnologia", "Cantidad"]
    fig_evol = px.area(evol_tec, x="Año", y="Cantidad", color="Tecnologia",
                       title="Evolución de proyectos por tecnología",
                       groupnorm=None)
    st.plotly_chart(fig_evol, use_container_width=True)

    st.subheader("Tendencias de inversión en el tiempo")
    inv_ano = df.groupby(df["Fecha_Entrada_Operacion"].dt.year)["Inversion_Inicial_MUSD"].sum().reset_index()
    fig_inv_time = px.line(inv_ano, x="Fecha_Entrada_Operacion", y="Inversion_Inicial_MUSD",
                           title="Inversión Total por Año (M USD)",
                           markers=True)
    fig_inv_time.update_traces(line_color="green", line_width=3)
    st.plotly_chart(fig_inv_time, use_container_width=True)

with tab5:
    st.subheader("Análisis estadístico con Seaborn")

    st.markdown("**Distribución de eficiencia por tecnología (boxplot)**")
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df, x="Tecnologia", y="Eficiencia_Planta_Pct", palette="Set2", ax=ax1)
    ax1.set_title("Eficiencia de Planta por Tecnología")
    ax1.set_xlabel("Tecnología")
    ax1.set_ylabel("Eficiencia (%)")
    plt.xticks(rotation=15)
    st.pyplot(fig1)

    st.markdown("**Frecuencia de estados de proyecto (countplot)**")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    orden_estado = df["Estado_Actual"].value_counts().index
    sns.countplot(data=df, y="Estado_Actual", order=orden_estado, palette="muted", ax=ax2)
    ax2.set_title("Cantidad de Proyectos por Estado Actual")
    ax2.set_xlabel("Cantidad")
    ax2.set_ylabel("Estado")
    st.pyplot(fig2)

    st.markdown("**Pairplot de variables numéricas**")
    num_vars = ["Capacidad_Instalada_MW", "Generacion_Diaria_MWh",
                "Eficiencia_Planta_Pct", "Inversion_Inicial_MUSD"]
    fig3 = sns.pairplot(df[num_vars], diag_kind="kde", corner=True)
    fig3.fig.suptitle("Relaciones entre variables numéricas", y=1.02)
    st.pyplot(fig3.figure)

    st.markdown("**Matriz de correlación (heatmap)**")
    fig4, ax4 = plt.subplots(figsize=(8, 6))
    corr = df[num_vars].corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r",
                square=True, linewidths=0.5, ax=ax4)
    ax4.set_title("Correlación entre variables numéricas")
    st.pyplot(fig4)

with tab6:
    st.subheader("Visualización clásica con Matplotlib (Pyplot)")

    st.markdown("**Histograma de eficiencia de planta**")
    fig5, ax5 = plt.subplots(figsize=(10, 5))
    ax5.hist(df["Eficiencia_Planta_Pct"], bins=30, color="steelblue",
             edgecolor="white", alpha=0.8)
    ax5.axvline(df["Eficiencia_Planta_Pct"].mean(), color="red",
                linestyle="--", linewidth=2, label=f"Media: {df['Eficiencia_Planta_Pct'].mean():.1f}%")
    ax5.set_title("Distribución de Eficiencia de Planta")
    ax5.set_xlabel("Eficiencia (%)")
    ax5.set_ylabel("Frecuencia")
    ax5.legend()
    st.pyplot(fig5)

    st.markdown("**Proyectos por año (gráfico de barras)**")
    counts_year = df["Fecha_Entrada_Operacion"].dt.year.value_counts().sort_index()
    fig6, ax6 = plt.subplots(figsize=(10, 5))
    colores = plt.cm.Oranges(np.linspace(0.3, 0.9, len(counts_year)))
    ax6.bar(counts_year.index, counts_year.values, color=colores, edgecolor="black")
    ax6.set_title("Proyectos por Año de Entrada en Operación")
    ax6.set_xlabel("Año")
    ax6.set_ylabel("Cantidad de Proyectos")
    for i, v in enumerate(counts_year.values):
        ax6.text(counts_year.index[i], v + 1, str(v), ha="center", fontweight="bold")
    st.pyplot(fig6)

    st.markdown("**Subplots: capacidad, generación e inversión**")
    fig7, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].hist(df["Capacidad_Instalada_MW"], bins=25, color="seagreen", edgecolor="white")
    axes[0].set_title("Capacidad Instalada (MW)")
    axes[0].set_xlabel("MW")
    axes[1].hist(df["Generacion_Diaria_MWh"], bins=25, color="teal", edgecolor="white")
    axes[1].set_title("Generación Diaria (MWh)")
    axes[1].set_xlabel("MWh")
    axes[2].hist(df["Inversion_Inicial_MUSD"], bins=25, color="coral", edgecolor="white")
    axes[2].set_title("Inversión Inicial (M USD)")
    axes[2].set_xlabel("M USD")
    plt.tight_layout()
    st.pyplot(fig7)

    st.markdown("**Scatter: Inversión vs Capacidad (con regresión)**")
    fig8, ax8 = plt.subplots(figsize=(10, 6))
    tecnologias = df["Tecnologia"].unique()
    colores_tec = plt.cm.tab10(np.linspace(0, 1, len(tecnologias)))
    for tec, color in zip(tecnologias, colores_tec):
        subset = df[df["Tecnologia"] == tec]
        ax8.scatter(subset["Capacidad_Instalada_MW"], subset["Inversion_Inicial_MUSD"],
                    label=tec, color=color, alpha=0.7, edgecolors="black", linewidth=0.5)
    z = np.polyfit(df["Capacidad_Instalada_MW"], df["Inversion_Inicial_MUSD"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df["Capacidad_Instalada_MW"].min(), df["Capacidad_Instalada_MW"].max(), 100)
    ax8.plot(x_line, p(x_line), color="gray", linestyle="--", linewidth=2, label="Tendencia lineal")
    ax8.set_title("Inversión vs Capacidad Instalada")
    ax8.set_xlabel("Capacidad Instalada (MW)")
    ax8.set_ylabel("Inversión Inicial (M USD)")
    ax8.legend(loc="upper left", fontsize=8)
    st.pyplot(fig8)

with tab7:
    st.subheader("Exportar Datos a Excel")
    st.markdown("Descarga los datos completos con resúmenes por tecnología, operador y estado en un archivo Excel.")

    buf_excel = io.BytesIO()
    with pd.ExcelWriter(buf_excel, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Datos Completos", index=False)

        resumen_tec = df.groupby("Tecnologia").agg(
            Proyectos=("ID_Proyecto", "count"),
            Capacidad_Total_MW=("Capacidad_Instalada_MW", "sum"),
            Generacion_Promedio_MWh=("Generacion_Diaria_MWh", "mean"),
            Eficiencia_Promedio_Pct=("Eficiencia_Planta_Pct", "mean"),
            Inversion_Total_MUSD=("Inversion_Inicial_MUSD", "sum")
        ).reset_index()
        resumen_tec.to_excel(writer, sheet_name="Por Tecnología", index=False)

        resumen_op = df.groupby("Operador").agg(
            Proyectos=("ID_Proyecto", "count"),
            Capacidad_Total_MW=("Capacidad_Instalada_MW", "sum"),
            Inversion_Total_MUSD=("Inversion_Inicial_MUSD", "sum")
        ).reset_index().sort_values("Proyectos", ascending=False)
        resumen_op.to_excel(writer, sheet_name="Por Operador", index=False)

        resumen_estado = df.groupby("Estado_Actual").agg(
            Proyectos=("ID_Proyecto", "count"),
            Capacidad_Total_MW=("Capacidad_Instalada_MW", "sum"),
            Inversion_Total_MUSD=("Inversion_Inicial_MUSD", "sum")
        ).reset_index()
        resumen_estado.to_excel(writer, sheet_name="Por Estado", index=False)

        kpi_data = pd.DataFrame({
            "Indicador": ["Total Proyectos", "Capacidad Total (MW)", "Generación Diaria (MWh)",
                          "Inversión Total (M USD)", "Proyectos en Operación Comercial",
                          "Proyectos No Conectados al SIN", "Año Más Activo"],
            "Valor": [df.shape[0], df["Capacidad_Instalada_MW"].sum(),
                      df["Generacion_Diaria_MWh"].sum(), df["Inversion_Inicial_MUSD"].sum(),
                      f"{en_operacion} ({pct_operacion:.1f}%)",
                      f"{no_conectados} ({no_conectados/df.shape[0]*100:.1f}%)",
                      int(max_ano['Año'])]
        })
        kpi_data.to_excel(writer, sheet_name="KPIs", index=False)

    st.download_button(
        label="Descargar Excel",
        data=buf_excel.getvalue(),
        file_name="reporte_energia_renovable.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()
    st.subheader("Descargar Reporte PDF")
    st.markdown("Genera un reporte PDF con las gráficas principales, tablas de resumen y conclusiones.")

    buf_pdf = io.BytesIO()
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Reporte de Energia Renovable", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Analisis de proyectos de energia renovable en Colombia", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Indicadores Clave", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    kpi_items = [
        f"Total de proyectos: {df.shape[0]}",
        f"Capacidad instalada total: {df['Capacidad_Instalada_MW'].sum():,.0f} MW",
        f"Generacion diaria total: {df['Generacion_Diaria_MWh'].sum():,.0f} MWh",
        f"Inversion total: {df['Inversion_Inicial_MUSD'].sum():,.0f} M USD",
        f"Proyectos en operacion comercial: {en_operacion} ({pct_operacion:.1f}%)",
        f"Proyectos no conectados al SIN: {no_conectados} ({no_conectados/df.shape[0]*100:.1f}%)",
    ]
    for item in kpi_items:
        pdf.cell(0, 7, f"  - {item}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Distribucion por Tecnologia", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    tec_resumen = df.groupby("Tecnologia").agg(
        Proyectos=("ID_Proyecto", "count"),
        Cap_MW=("Capacidad_Instalada_MW", "sum"),
        Eficiencia_Prom=("Eficiencia_Planta_Pct", "mean")
    ).reset_index()
    col_widths = [50, 30, 40, 40]
    headers = ["Tecnologia", "Proyectos", "Capacidad (MW)", "Eficiencia Prom (%)"]
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 8, h, border=1, align="C")
    pdf.ln()
    for _, row in tec_resumen.iterrows():
        pdf.cell(col_widths[0], 7, row["Tecnologia"], border=1)
        pdf.cell(col_widths[1], 7, str(row["Proyectos"]), border=1, align="C")
        pdf.cell(col_widths[2], 7, f"{row['Cap_MW']:,.0f}", border=1, align="C")
        pdf.cell(col_widths[3], 7, f"{row['Eficiencia_Prom']:.1f}%", border=1, align="C")
        pdf.ln()
    pdf.ln(5)

    fig_box_rep, ax_box_rep = plt.subplots(figsize=(10, 4))
    sns.boxplot(data=df, x="Tecnologia", y="Eficiencia_Planta_Pct", palette="Set2", ax=ax_box_rep)
    ax_box_rep.set_title("Eficiencia por Tecnologia")
    ax_box_rep.set_xlabel("")
    ax_box_rep.set_ylabel("Eficiencia (%)")
    plt.xticks(rotation=15)
    plt.tight_layout()
    buf_box = io.BytesIO()
    fig_box_rep.savefig(buf_box, format="png", dpi=150)
    plt.close(fig_box_rep)
    buf_box.seek(0)
    pdf.image(buf_box, x=10, w=180)
    pdf.ln(5)

    counts_year_pdf = df["Fecha_Entrada_Operacion"].dt.year.value_counts().sort_index()
    fig_year_rep, ax_year_rep = plt.subplots(figsize=(10, 4))
    ax_year_rep.bar(counts_year_pdf.index, counts_year_pdf.values, color="orange", edgecolor="black")
    ax_year_rep.set_title("Proyectos por Ano de Entrada en Operacion")
    ax_year_rep.set_xlabel("Ano")
    ax_year_rep.set_ylabel("Cantidad")
    plt.tight_layout()
    buf_year = io.BytesIO()
    fig_year_rep.savefig(buf_year, format="png", dpi=150)
    plt.close(fig_year_rep)
    buf_year.seek(0)
    pdf.image(buf_year, x=10, w=180)
    pdf.ln(5)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Top 10 Operadores por Inversion", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    inv_ops_pdf = df.groupby("Operador")["Inversion_Inicial_MUSD"].sum().reset_index().sort_values("Inversion_Inicial_MUSD", ascending=False).head(10)
    col_w2 = [60, 50]
    pdf.cell(col_w2[0], 8, "Operador", border=1, align="C")
    pdf.cell(col_w2[1], 8, "Inversion Total (M USD)", border=1, align="C")
    pdf.ln()
    for _, row in inv_ops_pdf.iterrows():
        pdf.cell(col_w2[0], 7, row["Operador"], border=1)
        pdf.cell(col_w2[1], 7, f"{row['Inversion_Inicial_MUSD']:,.1f}", border=1, align="C")
        pdf.ln()
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Conclusiones", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    conclusiones = [
        f"Mix tecnologico diversificado: {df['Tecnologia'].nunique()} tecnologias distintas operando en el pais.",
        f"Liderazgo en operacion: {top_ops.iloc[0]['Operador']} lidera en cantidad de proyectos con {top_ops.iloc[0]['Cantidad']} proyectos.",
        f"Sector en expansion: Solo {pct_operacion:.1f}% de los proyectos estan en operacion comercial, el resto esta en construccion, pruebas o planeacion.",
        f"Desafio de conectividad: {no_conectados/df.shape[0]*100:.1f}% de los proyectos no estan conectados al SIN, lo que representa una oportunidad de mejora en infraestructura de red.",
        f"Crecimiento variable: La actividad del sector ha tenido picos notables, con {int(max_ano['Año'])} como el ano mas activo."
    ]
    for c in conclusiones:
        pdf.multi_cell(0, 8, f"  - {c}")
        pdf.ln(2)

    pdf.output(buf_pdf)
    buf_pdf.seek(0)

    st.download_button(
        label="Descargar PDF",
        data=buf_pdf,
        file_name="reporte_energia_renovable.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.divider()
    st.subheader("Vista previa del reporte PDF")
    st.markdown("El reporte incluye:")
    st.markdown("- Indicadores clave del sector")
    st.markdown("- Tabla resumen por tecnología")
    st.markdown("- Gráfico de eficiencia por tecnología")
    st.markdown("- Proyectos por año")
    st.markdown("- Top 10 operadores por inversión")
    st.markdown("- Conclusiones del análisis")

with tab8:
    st.subheader("Chatbot de Cultura General e Historia Mundial")
    st.markdown("Haz preguntas sobre historia, geografía, ciencia, arte y cultura general.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe tu pregunta aquí...", accept_file=False):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not api_key:
            with st.chat_message("assistant"):
                st.warning("Ingresa tu API Key en la barra lateral para empezar a conversar.")
        else:
            try:
                client = Groq(api_key=api_key)
                system_msg = {
                    "role": "system",
                    "content": (
                        "Eres un experto en cultura general e historia mundial. "
                        "Respondes de forma clara, precisa y educativa. "
                        "Usas un tono amigable y accesible. "
                        "Cuando te pregunten sobre historia, incluyes contexto relevante, fechas y personajes clave. "
                        "Si no sabes algo, lo admites sin inventar."
                    )
                }
                chat_history = [system_msg]
                for m in st.session_state.messages:
                    chat_history.append({"role": m["role"], "content": m["content"]})
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=chat_history,
                    stream=True
                )
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    full_response = ""
                    for chunk in response:
                        content = chunk.choices[0].delta.content or ""
                        full_response += content
                        placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                with st.chat_message("assistant"):
                    st.error(f"Error: {e}", icon="🚨")

    if st.session_state.messages and st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

with tab9:
    st.subheader("Extractor de Datos desde Texto")
    st.markdown("Pega un párrafo con cifras para convertirlo en tabla y generar un EDA automático.")

    texto = st.text_area("Pega tu texto aquí", height=200, placeholder="Ej: En 2023 la empresa X vendió 1500 unidades en enero, 2300 en febrero y 1800 en marzo...")

    if st.button("Procesar con LLM", disabled=not api_key, type="primary"):
        if not api_key:
            st.warning("Ingresa tu API Key en la barra lateral.")
        elif not texto.strip():
            st.warning("Pega un texto antes de procesar.")
        else:
            with st.spinner("Extrayendo datos estructurados..."):
                try:
                    client = Groq(api_key=api_key)
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Eres un extractor de datos. Del siguiente texto, extrae toda la información "
                                    "numérica y categórica relevante y conviértela a formato CSV. "
                                    "La primera fila deben ser los encabezados. "
                                    "Devuelve SOLAMENTE el CSV, sin explicaciones, sin comillas triples, sin delimitadores de código."
                                )
                            },
                            {"role": "user", "content": texto}
                        ],
                        temperature=0.1
                    )
                    csv_text = resp.choices[0].message.content.strip()

                    lines = [l for l in csv_text.split("\n") if l.strip()]
                    csv_io = io.StringIO("\n".join(lines))
                    df_ext = pd.read_csv(csv_io)

                    if df_ext.empty:
                        st.error("No se pudo extraer una tabla del texto.")
                    else:
                        st.success(f"Tabla extraída: {df_ext.shape[0]} filas, {df_ext.shape[1]} columnas.")
                        st.subheader("Tabla extraída")
                        st.dataframe(df_ext, use_container_width=True)

                        st.subheader("Análisis Exploratorio (EDA)")

                        st.markdown("**Estadísticas descriptivas**")
                        st.dataframe(df_ext.describe(include="all").fillna(""), use_container_width=True)

                        num_cols = df_ext.select_dtypes(include=np.number).columns.tolist()
                        cat_cols = df_ext.select_dtypes(exclude=np.number).columns.tolist()

                        if num_cols:
                            for col in num_cols[:4]:
                                fig_hist = px.histogram(df_ext, x=col, title=f"Distribución de {col}", nbins=20)
                                st.plotly_chart(fig_hist, use_container_width=True)

                        if len(num_cols) >= 2:
                            fig_box = px.box(df_ext.melt(value_vars=num_cols[:6]), x="variable", y="value",
                                             title="Boxplots de variables numéricas")
                            st.plotly_chart(fig_box, use_container_width=True)

                            fig_corr = px.imshow(
                                df_ext[num_cols].corr(), text_auto=True, aspect="auto",
                                title="Matriz de correlación", color_continuous_scale="RdBu_r"
                            )
                            st.plotly_chart(fig_corr, use_container_width=True)

                            if len(num_cols) >= 2:
                                fig_scatter = px.scatter_matrix(df_ext[num_cols[:5]], title="Relaciones entre variables")
                                st.plotly_chart(fig_scatter, use_container_width=True)

                        if cat_cols:
                            for col in cat_cols[:3]:
                                counts = df_ext[col].value_counts().reset_index()
                                counts.columns = [col, "Cantidad"]
                                fig_bar = px.bar(counts, x=col, y="Cantidad",
                                                 title=f"Distribución de {col}", text_auto=True)
                                st.plotly_chart(fig_bar, use_container_width=True)

                        st.subheader("Análisis del LLM")
                        with st.spinner("Generando análisis..."):
                            analysis = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {
                                        "role": "system",
                                        "content": (
                                            "Eres un analista de datos. Resume los hallazgos clave de la siguiente tabla "
                                            "en 3-5 puntos. Sé conciso y numérico."
                                        )
                                    },
                                    {"role": "user", "content": df_ext.to_csv(index=False)}
                                ],
                                temperature=0.3
                            )
                            st.markdown(analysis.choices[0].message.content)

                except Exception as e:
                    st.error(f"Error al procesar: {e}", icon="🚨")
st.markdown(f"""
- **Mix tecnológico diversificado:** {df['Tecnologia'].nunique()} tecnologías distintas operando en el país.
- **Liderazgo en operación:** {top_ops.iloc[0]['Operador']} lidera en cantidad de proyectos,
  mientras que otros operadores compiten en capacidad e inversión.
- **Sector en expansión:** Solo {pct_operacion:.1f}% de los proyectos están en operación comercial,
  el resto está en construcción, pruebas o planeación.
- **Desafío de conectividad:** {no_conectados/df.shape[0]*100:.1f}% de los proyectos no están conectados al SIN,
  lo que representa una oportunidad de mejora en infraestructura de red.
- **Crecimiento variable:** La actividad del sector ha tenido picos notables, con {int(max_ano['Año'])} como el año más activo.
""")
