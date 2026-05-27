import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

#Configuración
st.set_page_config(
    page_title="ATUS · Dashboard Accidentes Viales México",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

#Estilos
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.block-container{padding-top:1.2rem;padding-bottom:2rem;}

.kpi-card{
  background:linear-gradient(135deg,#1a1f35 0%,#22273d 100%);
  border:1px solid #2d3358;border-radius:14px;
  padding:18px 20px;text-align:center;margin-bottom:4px;
}
.kpi-card.danger {border-color:#ff4b4b55;background:linear-gradient(135deg,#2a1818,#321f1f);}
.kpi-card.warning{border-color:#ffb30055;background:linear-gradient(135deg,#261d0a,#2e2510);}
.kpi-card.success{border-color:#00cc8855;background:linear-gradient(135deg,#0d2318,#122b1e);}
.kpi-card.info   {border-color:#4b8fff55;background:linear-gradient(135deg,#0f1a2d,#141f38);}
.kpi-card.purple {border-color:#a78bfa55;background:linear-gradient(135deg,#1a1230,#201638);}

.kpi-icon {font-size:1.9rem;margin-bottom:2px;}
.kpi-value{font-size:1.9rem;font-weight:700;color:#f0f2f6;line-height:1.1;}
.kpi-label{font-size:0.73rem;color:#8b95b0;text-transform:uppercase;letter-spacing:.06em;margin-top:4px;}
.kpi-sub  {font-size:0.68rem;color:#5a6280;margin-top:3px;}

.section-title{
  font-size:.95rem;font-weight:600;color:#c0c8e8;
  text-transform:uppercase;letter-spacing:.08em;
  border-left:3px solid #4b8fff;padding-left:10px;
  margin:24px 0 12px 0;
}
.insight-box{
  background:#141926;border:1px solid #1e2840;border-radius:10px;
  padding:14px 18px;margin-top:8px;color:#9ba8cc;font-size:.82rem;line-height:1.6;
}
.insight-box strong{color:#c8d4f8;}
.footer{text-align:center;color:#2e3558;font-size:.7rem;margin-top:40px;padding-top:20px;border-top:1px solid #1a2035;}
</style>
""", unsafe_allow_html=True)

#Carga de datos
DATA = "data/processed/summary"

def read_optional_summary(file_name):
    path = Path(DATA) / file_name
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data
def load():
    return {
        "cause":   pd.read_csv(f"{DATA}/accidents_by_cause.csv"),
        "classif": pd.read_csv(f"{DATA}/accidents_by_classification.csv"),
        "hour":    pd.read_csv(f"{DATA}/accidents_by_hour.csv"),
        "month":   pd.read_csv(f"{DATA}/accidents_by_month.csv"),
        "muni":    pd.read_csv(f"{DATA}/accidents_by_municipality.csv"),
        "state":   pd.read_csv(f"{DATA}/accidents_by_state.csv"),
        "type":    pd.read_csv(f"{DATA}/accidents_by_type.csv"),
        "trend":   pd.read_csv(f"{DATA}/annual_trend.csv"),
        "quality": pd.read_csv(f"{DATA}/data_quality_report.csv"),
        "metrics": pd.read_csv(f"{DATA}/run_metrics.csv"),
        "weekday": read_optional_summary("accidents_by_weekday.csv"),
        "zone":    read_optional_summary("accidents_by_zone.csv"),
    }

d = load()

# ─── Paleta / helpers ─────────────────────────────────────────────────────────
COLORS = ["#4b8fff","#ff6b6b","#ffd166","#06d6a0","#a78bfa",
          "#f97316","#34d399","#f472b6","#60a5fa","#fb923c"]

def base_layout(**kw):
    cfg = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c0c8e8", font_family="Inter, sans-serif",
        margin=dict(t=36,b=40,l=10,r=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_size=11),
        xaxis=dict(gridcolor="#1e2535", zerolinecolor="#1e2535"),
        yaxis=dict(gridcolor="#1e2535", zerolinecolor="#1e2535"),
    )
    cfg.update(kw)
    return cfg

def fmt(n): return f"{n:,.0f}"

#KPIs globales
total_acc   = d["trend"]["accidentes"].sum()
total_her   = d["trend"]["victimas_heridas"].sum()
total_mue   = d["trend"]["victimas_muertas"].sum()
acc_heridos = d["trend"]["accidentes_con_heridos"].sum()
acc_muertos = d["trend"]["accidentes_con_muertos"].sum()
sev_avg     = round(d["trend"]["indice_gravedad"].mean(), 4)

#Sidebar
with st.sidebar:
    st.markdown("ATUS Dashboard")
    st.markdown("**Sistema de Accidentes de Tránsito en Zonas Urbanas y Suburbanas**")
    st.markdown("---")
    section = st.radio("Ir a sección:", [
        "Resumen General",
        "Análisis por Estado",
        "Análisis por Municipio",
        "Distribución Horaria",
        "Tendencia Mensual",
        "Causas y Tipos",
        "Víctimas y Gravedad",
        "Ray vs Pandas",
    ])
    st.markdown("---")
    st.markdown(f"**Años:** 1999, 2010, 2022-2024")
    st.markdown(f"**Registros:** 1,892,726")
    st.markdown(f"**Municipios:** 1,984")
    st.markdown(f"**Estados:** 32")

#RESUMEN GENERAL
if section == "Resumen General":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">Resumen General</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#5a6690;margin-bottom:20px;">Indicadores agregados de siniestralidad vial en México · ATUS</p>', unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    cards = [
        (c1,"info",fmt(total_acc),"Total Accidentes","5 años analizados"),
        (c2,"warning",fmt(acc_heridos),"Con Heridos",f"{acc_heridos/total_acc*100:.1f}% del total"),
        (c3,"danger",fmt(acc_muertos),"Con Fallecidos",f"{acc_muertos/total_acc*100:.1f}% del total"),
        (c4,"success",fmt(total_her),"Víctimas Heridas",f"en {fmt(acc_heridos)} accidentes"),
        (c5,"purple",fmt(total_mue),"Víctimas Muertas",f"índice: {sev_avg}"),
    ]
    for col,cls,val,lbl,sub in cards:
        with col:
            st.markdown(f'<div class="kpi-value">{val}</div>'
                        f'<div class="kpi-label">{lbl}</div>'
                        f'<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Evolución Anual de Siniestralidad</div>', unsafe_allow_html=True)
    trend = d["trend"].sort_values("año")

    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=trend["año"],y=trend["accidentes"],name="Accidentes",
                         marker_color="#4b8fff",opacity=.85), secondary_y=False)
    fig.add_trace(go.Scatter(x=trend["año"],y=trend["victimas_heridas"],name="Heridos",
                             mode="lines+markers",line=dict(color="#ffd166",width=2.5),marker_size=9), secondary_y=True)
    fig.add_trace(go.Scatter(x=trend["año"],y=trend["victimas_muertas"],name="Fallecidos",
                             mode="lines+markers",line=dict(color="#ff4b4b",width=2.5,dash="dash"),marker_size=9), secondary_y=True)
    fig.add_trace(go.Scatter(x=trend["año"],y=trend["indice_gravedad"],name="Índice gravedad",
                             mode="lines+markers",line=dict(color="#06d6a0",width=2,dash="dot"),marker_size=7), secondary_y=True)
    fig.update_layout(**base_layout(height=360,hovermode="x unified",
                      yaxis_title="Accidentes",yaxis2_title="Víctimas / Índice",bargap=.3))
    fig.update_yaxes(gridcolor="#1e2535")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="insight-box"><strong>Insight:</strong> El número de accidentes creció de 285,494 en 1999 a 427,267 en 2010 (+50%), pero descendió en 2022-2024. El índice de gravedad muestra una <strong>mejora consistente</strong>: de 0.46 a 0.29, indicando que los accidentes recientes son menos letales.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Clasificación de Accidentes</div>', unsafe_allow_html=True)
    clf = d["classif"].copy()
    col1,col2 = st.columns([1,2])
    with col1:
        fig_pie = px.pie(clf,values="accidentes",names="clasificacion_accidente",
                         color_discrete_sequence=["#ff4b4b","#ffd166","#4b8fff"],hole=.55)
        fig_pie.update_traces(textposition="outside",textinfo="percent+label",
                              hovertemplate="%{label}: %{value:,}<extra></extra>")
        fig_pie.update_layout(**base_layout(height=310,showlegend=False,
                              title=dict(text="Distribución por Clasificación",font_size=13,x=0)))
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        clf["tasa_heridos"] = (clf["accidentes_con_heridos"]/clf["accidentes"]*100).round(1)
        clf["tasa_muertos"] = (clf["accidentes_con_muertos"]/clf["accidentes"]*100).round(1)
        fig_clf = go.Figure()
        for col_name,clr,nm in [("accidentes","#4b8fff","Total"),
                                  ("accidentes_con_heridos","#ffd166","Con heridos"),
                                  ("accidentes_con_muertos","#ff4b4b","Con fallecidos")]:
            fig_clf.add_trace(go.Bar(x=clf["clasificacion_accidente"],y=clf[col_name],
                                     name=nm,marker_color=clr,opacity=.9))
        fig_clf.update_layout(**base_layout(height=310,barmode="group",
                              title=dict(text="Volumen por Clasificación",font_size=13,x=0)))
        st.plotly_chart(fig_clf, use_container_width=True)

#ANÁLISIS POR ESTADO
elif section == "Análisis por Estado":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿Qué estados concentran más accidentes?</h1>', unsafe_allow_html=True)

    state = d["state"].copy()
    state["pct_heridos"] = (state["accidentes_con_heridos"]/state["accidentes"]*100).round(1)
    state["pct_muertos"] = (state["accidentes_con_muertos"]/state["accidentes"]*100).round(1)
    state["mortalidad_100k"] = (state["victimas_muertas"]/state["accidentes"]*100000).round(0)

    tab1,tab2,tab3 = st.tabs(["Ranking por Volumen","Ranking por Gravedad","Comparativo Completo"])

    with tab1:
        st.markdown('<div class="section-title">Top 15 Estados · Total de Accidentes</div>', unsafe_allow_html=True)
        top = state.sort_values("accidentes",ascending=False).head(15)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=top["entidad"][::-1],x=top["accidentes"][::-1],
                             orientation="h",name="Total",marker_color="#4b8fff",opacity=.88,
                             hovertemplate="%{y}: %{x:,} accidentes<extra></extra>"))
        fig.add_trace(go.Bar(y=top["entidad"][::-1],x=top["accidentes_con_heridos"][::-1],
                             orientation="h",name="Con heridos",marker_color="#ffd166",opacity=.88))
        fig.add_trace(go.Bar(y=top["entidad"][::-1],x=top["accidentes_con_muertos"][::-1],
                             orientation="h",name="Con fallecidos",marker_color="#ff4b4b",opacity=.88))
        fig.update_layout(**base_layout(height=520,barmode="overlay",
                          yaxis=dict(gridcolor="rgba(0,0,0,0)",tickfont_size=11)))
        st.plotly_chart(fig, use_container_width=True)

        c1,c2,c3 = st.columns(3)
        top1 = state.sort_values("accidentes",ascending=False).iloc[0]
        with c1:
            st.markdown(f'<div class="kpi-value">{top1["entidad"]}</div>'
                        f'<div class="kpi-label">Mayor siniestralidad</div>'
                        f'<div class="kpi-sub">{fmt(top1["accidentes"])} accidentes</div></div>', unsafe_allow_html=True)
        bot1 = state.sort_values("accidentes").iloc[0]
        with c2:
            st.markdown(f'<div class="kpi-value">{bot1["entidad"]}</div>'
                        f'<div class="kpi-label">Menor siniestralidad</div>'
                        f'<div class="kpi-sub">{fmt(bot1["accidentes"])} accidentes</div></div>', unsafe_allow_html=True)
        with c3:
            avg_acc = state["accidentes"].mean()
            st.markdown(f'<div class="kpi-value">{fmt(avg_acc)}</div>'
                        f'<div class="kpi-label">Promedio por estado</div>'
                        f'<div class="kpi-sub">mediana: {fmt(state["accidentes"].median())}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="insight-box"><strong>Nuevo León</strong> lidera con 354,631 accidentes (casi 3× el promedio nacional de ~57,500), seguido por <strong>Chihuahua</strong> y <strong>Jalisco</strong>. Estos 3 estados concentran el <strong>33%</strong> del total nacional.</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-title">Índice de Gravedad por Estado</div>', unsafe_allow_html=True)
        grav = state.sort_values("indice_gravedad",ascending=False)
        fig2 = px.bar(grav,x="entidad",y="indice_gravedad",
                      color="indice_gravedad",color_continuous_scale="RdYlGn_r",
                      text="indice_gravedad",
                      hover_data={"victimas_muertas":True,"accidentes":True})
        fig2.update_traces(texttemplate="%{text:.3f}",textposition="outside",textfont_size=9)
        fig2.update_layout(**base_layout(height=420,xaxis_tickangle=-45,xaxis_tickfont_size=9,
                           coloraxis_showscale=False,
                           title=dict(text="Mayor índice = más víctimas por accidente",font_size=12,x=0)))
        st.plotly_chart(fig2, use_container_width=True)

        # Scatter: volumen vs gravedad
        fig3 = px.scatter(state,x="accidentes",y="indice_gravedad",
                          size="victimas_muertas",color="indice_gravedad",
                          text="entidad",color_continuous_scale="RdYlGn_r",
                          size_max=50,
                          hover_data={"victimas_heridas":True,"victimas_muertas":True})
        fig3.update_traces(textposition="top center",textfont_size=9)
        fig3.update_layout(**base_layout(height=440,coloraxis_showscale=False,
                           xaxis_title="Volumen de accidentes",yaxis_title="Índice de gravedad",
                           title=dict(text="Volumen vs Gravedad (tamaño = fallecidos)",font_size=12,x=0)))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box"><strong>Sinaloa</strong> (0.84) y <strong>Yucatán</strong> (0.68) tienen los índices de gravedad más altos, muy por encima del promedio nacional (~0.38). Nótese que <strong>Nuevo León</strong> lidera en volumen pero tiene gravedad baja (0.15), mientras que estados pequeños como <strong>Zacatecas</strong> muestran alta letalidad relativa.</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-title">Tabla Comparativa · Todos los Estados</div>', unsafe_allow_html=True)
        tbl = state[["entidad","accidentes","accidentes_con_heridos","accidentes_con_muertos",
                     "victimas_heridas","victimas_muertas","indice_gravedad","pct_heridos","pct_muertos"]].copy()
        tbl.columns = ["Estado","Accidentes","Con Heridos","Con Fallecidos",
                       "Víctimas Heridas","Víctimas Muertas","Índ. Gravedad","% Heridos","% Mortales"]
        tbl = tbl.sort_values("Accidentes",ascending=False).reset_index(drop=True)
        tbl.index += 1
        st.dataframe(tbl.style
            .background_gradient(subset=["Accidentes"],cmap="Blues")
            .background_gradient(subset=["Índ. Gravedad"],cmap="RdYlGn_r")
            .format({"Accidentes":"{:,.0f}","Con Heridos":"{:,.0f}","Con Fallecidos":"{:,.0f}",
                     "Víctimas Heridas":"{:,.0f}","Víctimas Muertas":"{:,.0f}",
                     "Índ. Gravedad":"{:.3f}","% Heridos":"{:.1f}%","% Mortales":"{:.2f}%"}),
            use_container_width=True, height=600)

#ANÁLISIS POR MUNICIPIO
elif section == "Análisis por Municipio":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿Qué municipios presentan mayor siniestralidad?</h1>', unsafe_allow_html=True)

    muni = d["muni"].copy()
    muni["municipio_full"] = muni["municipio"] + " (" + muni["entidad"] + ")"
    muni["pct_mortales"] = (muni["accidentes_con_muertos"]/muni["accidentes"]*100).round(2)

    col_filter, _ = st.columns([2,3])
    with col_filter:
        min_acc = st.slider("Accidentes mínimos para análisis de gravedad", 50, 2000, 200, 50)

    tab1,tab2,tab3 = st.tabs(["Top 20 Volumen","Top 20 Gravedad","Tabla Completa"])

    with tab1:
        top20 = muni.sort_values("accidentes",ascending=False).head(20)
        fig = go.Figure()
        for col_,clr,nm in [("accidentes","#4b8fff","Total"),("accidentes_con_heridos","#ffd166","Heridos"),
                             ("accidentes_con_muertos","#ff4b4b","Fallecidos")]:
            fig.add_trace(go.Bar(y=top20["municipio_full"][::-1],x=top20[col_][::-1],
                                 orientation="h",name=nm,marker_color=clr,opacity=.88))
        fig.update_layout(**base_layout(height=580,barmode="overlay",
                          yaxis=dict(gridcolor="rgba(0,0,0,0)",tickfont_size=10)))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box">Los municipios más accidentados son capitales o zonas metropolitanas. <strong>Monterrey, Chihuahua y Guadalajara</strong> concentran la mayor parte de accidentes por alta densidad vehicular y urbana.</div>', unsafe_allow_html=True)

    with tab2:
        top_grav = muni[muni["accidentes"]>=min_acc].sort_values("indice_gravedad",ascending=False).head(20)
        fig2 = px.bar(top_grav,x="indice_gravedad",y="municipio_full",
                      orientation="h",color="indice_gravedad",
                      color_continuous_scale="RdYlGn_r",
                      text="indice_gravedad",
                      hover_data={"accidentes":True,"victimas_muertas":True,"entidad":True})
        fig2.update_traces(texttemplate="%{text:.3f}",textposition="outside",textfont_size=10)
        fig2.update_layout(**base_layout(height=560,coloraxis_showscale=False,
                           xaxis=dict(gridcolor="#1e2535",zerolinecolor="#1e2535"),
                           yaxis=dict(gridcolor="rgba(0,0,0,0)",tickfont_size=10),
                           title=dict(text=f"Municipios con ≥{min_acc} accidentes",font_size=12,x=0)))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown(f'<div class="insight-box">Filtrando municipios con al menos {min_acc} accidentes. Municipios rurales y de tránsito de alta velocidad (carreteras) tienden a tener <strong>mayor índice de gravedad</strong> que las ciudades, donde la velocidad es más baja.</div>', unsafe_allow_html=True)

    with tab3:
        search = st.text_input("Buscar municipio o estado:", "")
        tbl = muni[["municipio","entidad","accidentes","accidentes_con_heridos",
                     "accidentes_con_muertos","victimas_heridas","victimas_muertas",
                     "indice_gravedad","pct_mortales"]].copy()
        tbl.columns = ["Municipio","Estado","Accidentes","Con Heridos","Con Fallecidos",
                       "Víctimas Heridas","Víctimas Muertas","Índ. Gravedad","% Mortales"]
        if search:
            mask = (tbl["Municipio"].str.contains(search,case=False,na=False) |
                    tbl["Estado"].str.contains(search,case=False,na=False))
            tbl = tbl[mask]
        tbl = tbl.sort_values("Accidentes",ascending=False).reset_index(drop=True)
        tbl.index += 1
        st.dataframe(tbl.style
            .background_gradient(subset=["Accidentes"],cmap="Blues")
            .background_gradient(subset=["Índ. Gravedad"],cmap="RdYlGn_r")
            .format({"Accidentes":"{:,.0f}","Con Heridos":"{:,.0f}","Con Fallecidos":"{:,.0f}",
                     "Víctimas Heridas":"{:,.0f}","Víctimas Muertas":"{:,.0f}",
                     "Índ. Gravedad":"{:.3f}","% Mortales":"{:.2f}%"}),
            use_container_width=True, height=500)
        st.caption(f"{len(tbl):,} municipios mostrados")

#DISTRIBUCIÓN HORARIA
elif section == "Distribución Horaria":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿En qué horarios ocurren más accidentes?</h1>', unsafe_allow_html=True)

    hour = d["hour"].dropna(subset=["hora"]).sort_values("hora").copy()
    hour["hora"] = hour["hora"].astype(int)
    hour["turno"] = hour["hora"].apply(lambda h:
        "Mañana (6-12h)" if 6<=h<12 else
        "Tarde (12-18h)" if 12<=h<18 else
        "Noche (18-24h)" if 18<=h<24 else "Madrugada (0-6h)")
    turno_colors = {
        "Mañana (6-12h)":"#ffd166",
        "Tarde (12-18h)":"#4b8fff",
        "Noche (18-24h)":"#a78bfa",
        "Madrugada (0-6h)":"#ff6b6b",
    }
    hour["color"] = hour["turno"].map(turno_colors)

    # Estadísticas por turno
    turno_stats = hour.groupby("turno").agg(
        accidentes=("accidentes","sum"),
        heridos=("victimas_heridas","sum"),
        muertos=("victimas_muertas","sum"),
    ).reset_index()
    turno_stats["grav"] = (turno_stats["muertos"]/turno_stats["accidentes"]*100).round(2)

    tab1,tab2,tab3,tab4 = st.tabs(["Distribución por Hora"," Análisis por Turno","Mapa de Calor","Día de Semana"])

    with tab1:
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Bar(x=hour["hora"],y=hour["accidentes"],
                             marker_color=hour["color"].tolist(),opacity=.88,name="Accidentes",
                             hovertemplate="Hora %{x}:00 → %{y:,} accidentes<extra></extra>"),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=hour["hora"],y=hour["accidentes_con_muertos"],
                                 name="Con fallecidos",mode="lines+markers",
                                 line=dict(color="#ff4b4b",width=2.5),marker_size=7),
                      secondary_y=True)
        fig.add_trace(go.Scatter(x=hour["hora"],y=hour["indice_gravedad"],
                                 name="Índice gravedad",mode="lines",
                                 line=dict(color="#06d6a0",width=2,dash="dot")),
                      secondary_y=True)
        fig.update_layout(**base_layout(height=380,hovermode="x unified",
                          yaxis_title="Número de accidentes",yaxis2_title="Fallecidos / Índice",
                          xaxis=dict(tickmode="linear",dtick=1,gridcolor="#1e2535",zerolinecolor="#1e2535")))
        fig.update_yaxes(gridcolor="#1e2535")
        st.plotly_chart(fig, use_container_width=True)

        hour_clean = hour.dropna(subset=["hora","accidentes","accidentes_con_muertos","indice_gravedad"])
        peak_acc  = hour_clean.loc[hour_clean["accidentes"].idxmax()]
        peak_mor  = hour_clean.loc[hour_clean["accidentes_con_muertos"].idxmax()]
        peak_grav = hour_clean.loc[hour_clean["indice_gravedad"].idxmax()]
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="kpi-value">{int(peak_acc["hora"])}:00h</div>'
                        f'<div class="kpi-label">Hora pico (volumen)</div>'
                        f'<div class="kpi-sub">{fmt(peak_acc["accidentes"])} accidentes</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-value">{int(peak_mor["hora"])}:00h</div>'
                        f'<div class="kpi-label">Hora más letal</div>'
                        f'<div class="kpi-sub">{fmt(peak_mor["accidentes_con_muertos"])} fallecidos</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="kpi-value">{int(peak_grav["hora"])}:00h</div>'
                        f'<div class="kpi-label">Mayor gravedad</div>'
                        f'<div class="kpi-sub">índice: {peak_grav["indice_gravedad"]:.3f}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="insight-box">Los accidentes se concentran entre las <strong>7-9h</strong> (hora de entrada) y <strong>18-20h</strong> (hora de salida). Sin embargo, la <strong>madrugada</strong> presenta el mayor índice de gravedad por menor tráfico y mayor velocidad.</div>', unsafe_allow_html=True)

    with tab2:
        fig2 = px.bar(turno_stats,x="turno",y="accidentes",
                      color="turno",color_discrete_map={k:v for k,v in turno_colors.items()},
                      text="accidentes")
        fig2.update_traces(texttemplate="%{text:,}",textposition="outside")
        fig2.update_layout(**base_layout(height=320,showlegend=False,
                           title=dict(text="Accidentes por Turno del Día",font_size=13,x=0)))
        st.plotly_chart(fig2, use_container_width=True)

        fig3 = make_subplots(rows=1,cols=3,subplot_titles=["Accidentes","Heridos","Fallecidos"])
        for i,(col_,nm) in enumerate([("accidentes","Acc."),("heridos","Her."),("muertos","Fall.")],1):
            fig3.add_trace(go.Bar(x=turno_stats["turno"],y=turno_stats[col_],
                                  marker_color=[turno_colors[t] for t in turno_stats["turno"]],
                                  showlegend=False,opacity=.88), row=1, col=i)
        fig3.update_layout(**base_layout(height=300))
        fig3.update_xaxes(tickangle=-20,tickfont_size=9)
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        # Heatmap polar: horas en círculo
        hour_circ = hour.copy()
        hour_circ["hora_label"] = hour_circ["hora"].astype(str).str.zfill(2) + ":00"
        fig4 = go.Figure(go.Barpolar(
            r=hour_circ["accidentes"],
            theta=hour_circ["hora"]*15,
            width=[15]*25,
            marker=dict(
                color=hour_circ["accidentes"],
                colorscale="Blues",
                showscale=True,
                colorbar=dict(title="Accidentes",thickness=12),
            ),
            hovertemplate="%{customdata}: %{r:,} accidentes<extra></extra>",
            customdata=hour_circ["hora_label"],
        ))
        fig4.update_layout(
            **{k:v for k,v in base_layout(height=480).items() if k not in ["xaxis","yaxis"]},
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(showticklabels=False,gridcolor="#1e2535"),
                angularaxis=dict(
                    tickvals=list(range(0,360,15)),
                    ticktext=[f"{h:02d}h" for h in range(24)],
                    gridcolor="#1e2535",color="#8b95b0",
                ),
            ),
            title=dict(text="Distribución Radial de Accidentes por Hora",font_size=13,x=0),
        )
        st.plotly_chart(fig4, use_container_width=True)

    with tab4:
        weekday = d["weekday"].copy()
        if weekday.empty:
            st.info("Ejecuta nuevamente el pipeline para generar accidents_by_weekday.csv.")
        else:
            weekday_order = {
                "Lunes": 1,
                "Martes": 2,
                "Miércoles": 3,
                "Jueves": 4,
                "Viernes": 5,
                "Sábado": 6,
                "Domingo": 7,
            }
            weekday["orden"] = weekday["dia_semana"].map(weekday_order).fillna(99)
            weekday = weekday.sort_values("orden")
            fig5 = make_subplots(specs=[[{"secondary_y": True}]])
            fig5.add_trace(go.Bar(
                x=weekday["dia_semana"], y=weekday["accidentes"],
                name="Accidentes", marker_color="#4b8fff", opacity=.88,
                hovertemplate="%{x}: %{y:,} accidentes<extra></extra>",
            ), secondary_y=False)
            fig5.add_trace(go.Scatter(
                x=weekday["dia_semana"], y=weekday["indice_gravedad"],
                name="Índice gravedad", mode="lines+markers",
                line=dict(color="#ff6b6b", width=2.5), marker_size=9,
            ), secondary_y=True)
            fig5.update_layout(**base_layout(height=360, hovermode="x unified",
                               title=dict(text="Accidentes e Índice de Gravedad por Día", font_size=13, x=0)))
            fig5.update_yaxes(title_text="Accidentes", secondary_y=False)
            fig5.update_yaxes(title_text="Índice de gravedad", secondary_y=True)
            st.plotly_chart(fig5, use_container_width=True)

            peak_day = weekday.loc[weekday["accidentes"].idxmax()]
            grave_day = weekday.loc[weekday["indice_gravedad"].idxmax()]
            st.markdown(
                f'<div class="insight-box">El día con más accidentes es <strong>{peak_day["dia_semana"]}</strong> '
                f'con <strong>{fmt(peak_day["accidentes"])}</strong> casos. '
                f'El mayor índice de gravedad aparece en <strong>{grave_day["dia_semana"]}</strong> '
                f'con valor <strong>{grave_day["indice_gravedad"]:.3f}</strong>.</div>',
                unsafe_allow_html=True,
            )

#TENDENCIA MENSUAL
elif section == "Tendencia Mensual":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿Qué meses presentan mayor incidencia?</h1>', unsafe_allow_html=True)

    month = d["month"].copy()
    mes_names = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                 7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    month["mes_nombre"] = month["mes"].map(mes_names)
    years = sorted(month["año"].unique())

    tab1,tab2,tab3 = st.tabs(["Por Año","Promedio Mensual","Mapa de Calor"])

    with tab1:
        metric = st.selectbox("Métrica:", ["accidentes","victimas_heridas","victimas_muertas","indice_gravedad"])
        metric_labels = {"accidentes":"Accidentes","victimas_heridas":"Víctimas Heridas",
                         "victimas_muertas":"Víctimas Muertas","indice_gravedad":"Índice de Gravedad"}
        yr_colors = {"1999":"#4b8fff","2010":"#ffd166","2022":"#06d6a0","2023":"#f97316","2024":"#a78bfa"}
        fig = go.Figure()
        for yr in years:
            sub = month[month["año"]==yr].sort_values("mes")
            fig.add_trace(go.Scatter(
                x=sub["mes_nombre"], y=sub[metric], name=str(yr),
                mode="lines+markers",
                line=dict(color=yr_colors.get(str(yr),"#ccc"),width=2.5),
                marker_size=8,
                hovertemplate=f"{yr} - %{{x}}: %{{y:,.1f}}<extra></extra>",
            ))
        fig.update_layout(**base_layout(height=380,yaxis_title=metric_labels[metric],
                          hovermode="x unified",
                          title=dict(text=f"{metric_labels[metric]} por Mes y Año",font_size=13,x=0)))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box"><strong>Diciembre</strong> y <strong>Enero</strong> suelen ser los meses con mayor siniestralidad, asociados a festividades y mayor tráfico. El mes de <strong>Febrero</strong> consistentemente muestra los valores más bajos (menos días y comportamiento post-festivo).</div>', unsafe_allow_html=True)

    with tab2:
        agg_mes = month.groupby("mes").agg(
            acc_mean=("accidentes","mean"),
            acc_std=("accidentes","std"),
            her_mean=("victimas_heridas","mean"),
            mue_mean=("victimas_muertas","mean"),
        ).reset_index()
        agg_mes["mes_nombre"] = agg_mes["mes"].map(mes_names)
        agg_mes["acc_std"] = agg_mes["acc_std"].fillna(0)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=agg_mes["mes_nombre"],y=agg_mes["acc_mean"],
                              name="Prom. accidentes",marker_color="#4b8fff",opacity=.85,
                              error_y=dict(type="data",array=agg_mes["acc_std"],visible=True,
                                           color="rgba(75,143,255,0.33)")))
        fig2.add_trace(go.Scatter(x=agg_mes["mes_nombre"],y=agg_mes["her_mean"],
                                  name="Prom. heridos",mode="lines+markers",
                                  line=dict(color="#ffd166",width=2),marker_size=7,yaxis="y2"))
        fig2.add_trace(go.Scatter(x=agg_mes["mes_nombre"],y=agg_mes["mue_mean"],
                                  name="Prom. fallecidos",mode="lines+markers",
                                  line=dict(color="#ff4b4b",width=2,dash="dash"),marker_size=7,yaxis="y2"))
        fig2.update_layout(**base_layout(height=380,barmode="group",
                           yaxis2=dict(overlaying="y",side="right",gridcolor="rgba(0,0,0,0)"),
                           title=dict(text="Promedio Mensual (todos los años disponibles)",font_size=13,x=0),
                           hovermode="x unified"))
        st.plotly_chart(fig2, use_container_width=True)

        # Ranking mensual
        rank_mes = agg_mes.sort_values("acc_mean",ascending=False)
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="kpi-value">{rank_mes.iloc[0]["mes_nombre"]}</div>'
                        f'<div class="kpi-label">Mes más accidentado</div>'
                        f'<div class="kpi-sub">Prom. {rank_mes.iloc[0]["acc_mean"]:,.0f} acc.</div></div>', unsafe_allow_html=True)
        with c2:
            best = rank_mes.iloc[-1]
            st.markdown(f'<div class="kpi-value">{best["mes_nombre"]}</div>'
                        f'<div class="kpi-label">Mes menos accidentado</div>'
                        f'<div class="kpi-sub">Prom. {best["acc_mean"]:,.0f} acc.</div></div>', unsafe_allow_html=True)
        with c3:
            variacion = ((rank_mes.iloc[0]["acc_mean"]-rank_mes.iloc[-1]["acc_mean"])/rank_mes.iloc[-1]["acc_mean"]*100)
            st.markdown(f'<div class="kpi-value">+{variacion:.1f}%</div>'
                        f'<div class="kpi-label">Variación pico-valle</div>'
                        f'<div class="kpi-sub">entre el mes más y menos crítico</div></div>', unsafe_allow_html=True)

    with tab3:
        # pivot = month.pivot_table(index="año",columns="mes_nombre",values="accidentes")
        mes_order = list(mes_names.values())
        # pivot = pivot.reindex(columns=mes_order)
        # fig3 = px.imshow(pivot,color_continuous_scale="Blues",aspect="auto",text_auto=True)
        # fig3.update_traces(texttemplate="%{z:,}",textfont_size=11,
        #                    hovertemplate="<b>%{y} - %{x}</b><br>Accidentes: %{z:,}<extra></extra>")
        # fig3.update_layout(**base_layout(height=280,coloraxis_showscale=False))
        # st.plotly_chart(fig3, use_container_width=True)

        # índice de gravedad mensual
        pivot_g = month.pivot_table(index="año",columns="mes_nombre",values="indice_gravedad")
        pivot_g = pivot_g.reindex(columns=mes_order)
        fig4 = px.imshow(pivot_g,color_continuous_scale="RdYlGn_r",aspect="auto",text_auto=True)
        fig4.update_traces(texttemplate="%{z:.3f}",textfont_size=11)
        fig4.update_layout(**base_layout(height=280,coloraxis_showscale=False,
                           title=dict(text="Índice de Gravedad por Mes y Año",font_size=13,x=0)))
        st.plotly_chart(fig4, use_container_width=True)

#CAUSAS Y TIPOS
elif section == "Causas y Tipos":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿Qué causas y tipos de accidentes son más frecuentes?</h1>', unsafe_allow_html=True)

    tab1,tab2,tab3 = st.tabs(["Causas","Tipos de Accidente","Análisis Cruzado"])

    with tab1:
        cause = d["cause"].sort_values("accidentes",ascending=False)
        fig = make_subplots(rows=1,cols=2,
            subplot_titles=("Volumen de Accidentes por Causa","Índice de Gravedad por Causa"))
        fig.add_trace(go.Bar(y=cause["causa_accidente"],x=cause["accidentes"],
                             orientation="h",marker_color="#4b8fff",opacity=.88,
                             name="Accidentes",showlegend=False),row=1,col=1)
        fig.add_trace(go.Bar(y=cause["causa_accidente"],x=cause["indice_gravedad"],
                             orientation="h",
                             marker=dict(color=cause["indice_gravedad"],colorscale="RdYlGn_r"),
                             name="Gravedad",showlegend=False),row=1,col=2)
        fig.update_layout(**base_layout(height=300))
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        # Donut por causa
        fig2 = px.pie(cause,values="accidentes",names="causa_accidente",
                      color_discrete_sequence=COLORS[:4],hole=.5)
        fig2.update_traces(textposition="outside",textinfo="percent+label",
                           hovertemplate="%{label}: %{value:,}<extra></extra>")
        fig2.update_layout(**base_layout(height=330,showlegend=False,
                           title=dict(text="Distribución de Causas",font_size=13,x=0)))
        col1,col2 = st.columns([1,2])
        with col1:
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            pct_conductor = cause[cause["causa_accidente"]=="Conductor"]["accidentes"].sum()/cause["accidentes"].sum()*100
            st.markdown(f"""
            <div class="insight-box">
            <strong>El factor humano domina absolutamente</strong>: "Conductor" representa el <strong>{pct_conductor:.1f}%</strong> de todos los accidentes (1,694,236 casos).<br><br>
            <strong>Conductor:</strong> {fmt(cause[cause['causa_accidente']=='Conductor']['accidentes'].sum())} acc. · gravedad 0.35<br>
            <strong>Mala condición del camino:</strong> {fmt(cause[cause['causa_accidente']=='Mala condición del camino']['accidentes'].sum())} acc. · gravedad 0.32<br>
            <strong>Falla del vehículo:</strong> {fmt(cause[cause['causa_accidente']=='Falla del vehículo']['accidentes'].sum())} acc. · gravedad 0.46<br><br>
            Las <strong>fallas del vehículo</strong> tienen el índice de gravedad más alto (0.46), indicando que cuando el auto falla el accidente tiende a ser más severo.
            </div>""", unsafe_allow_html=True)

    with tab2:
        typ = d["type"].sort_values("accidentes",ascending=False)
        # Treemap
        fig3 = px.treemap(typ,path=["tipo_accidente"],values="accidentes",
                          color="indice_gravedad",color_continuous_scale="RdYlGn_r",
                          hover_data={"victimas_muertas":True,"indice_gravedad":":.3f"})
        fig3.update_layout(**{k:v for k,v in base_layout(height=380).items()
                             if k not in ["xaxis","yaxis"]},
                           coloraxis_showscale=True,
                           coloraxis_colorbar=dict(title="Gravedad",thickness=12))
        st.plotly_chart(fig3, use_container_width=True)

        # Barras por tipo
        typ_s = typ.sort_values("accidentes",ascending=True)
        fig4 = go.Figure(go.Bar(
            y=typ_s["tipo_accidente"],x=typ_s["accidentes"],orientation="h",
            marker=dict(color=typ_s["indice_gravedad"],colorscale="RdYlGn_r",
                        showscale=True,colorbar=dict(title="Índice<br>Gravedad",thickness=12)),
            hovertemplate="<b>%{y}</b><br>Accidentes: %{x:,}<extra></extra>",
        ))
        fig4.update_layout(**base_layout(height=400,
                           title=dict(text="Accidentes por Tipo (color = gravedad)",font_size=13,x=0),
                           yaxis=dict(gridcolor="rgba(0,0,0,0)")))
        st.plotly_chart(fig4, use_container_width=True)

    with tab3:
        # Scatter: volumen vs gravedad por tipo
        fig5 = px.scatter(d["type"],x="accidentes",y="indice_gravedad",
                          size="victimas_muertas",color="indice_gravedad",
                          text="tipo_accidente",color_continuous_scale="RdYlGn_r",
                          size_max=60)
        fig5.update_traces(textposition="top center",textfont_size=9,
                           hovertemplate="<b>%{text}</b><br>Accidentes: %{x:,}<br>Gravedad: %{y:.3f}<extra></extra>")
        fig5.update_layout(**base_layout(height=440,coloraxis_showscale=False,
                           xaxis_title="Volumen de accidentes",yaxis_title="Índice de gravedad",
                           title=dict(text="Volumen vs Gravedad por Tipo (tamaño = fallecidos)",font_size=12,x=0)))
        st.plotly_chart(fig5, use_container_width=True)
        st.markdown('<div class="insight-box"><strong>Colisión con vehículo automotor</strong> domina en volumen (1.18M) pero tiene baja gravedad (0.20). En contraste, <strong>Atropellamiento</strong> y <strong>Volcadura</strong> combinan alto volumen con alta letalidad — son los tipos más críticos para políticas de prevención.</div>', unsafe_allow_html=True)

#VÍCTIMAS Y GRAVEDAD
elif section == "Víctimas y Gravedad":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿Dónde hay más víctimas heridas o fallecidas?</h1>', unsafe_allow_html=True)

    tab1,tab2,tab3,tab4 = st.tabs(["Por Estado","Por Municipio","Análisis de Gravedad","Por Zona"])

    with tab1:
        state = d["state"].copy()
        state["ratio_her_acc"] = (state["victimas_heridas"]/state["accidentes"]).round(3)
        state["ratio_mue_acc"] = (state["victimas_muertas"]/state["accidentes"]*1000).round(2)

        col1,col2 = st.columns(2)
        with col1:
            fig = px.bar(state.sort_values("victimas_heridas",ascending=False),
                         x="entidad",y="victimas_heridas",color="ratio_her_acc",
                         color_continuous_scale="YlOrRd",
                         title="Víctimas Heridas por Estado",
                         hover_data={"accidentes":True,"ratio_her_acc":True})
            fig.update_layout(**base_layout(height=370,xaxis_tickangle=-45,xaxis_tickfont_size=9,
                               coloraxis_showscale=False))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.bar(state.sort_values("victimas_muertas",ascending=False),
                          x="entidad",y="victimas_muertas",color="ratio_mue_acc",
                          color_continuous_scale="RdPu",
                          title="Víctimas Fallecidas por Estado",
                          hover_data={"accidentes":True,"ratio_mue_acc":True})
            fig2.update_layout(**base_layout(height=370,xaxis_tickangle=-45,xaxis_tickfont_size=9,
                               coloraxis_showscale=False))
            st.plotly_chart(fig2, use_container_width=True)

        # Tabla de víctimas
        vic_tbl = state[["entidad","victimas_heridas","victimas_muertas","total_victimas",
                          "indice_gravedad","ratio_her_acc","ratio_mue_acc"]].copy()
        vic_tbl.columns = ["Estado","Heridos","Fallecidos","Total Víctimas",
                           "Índ. Gravedad","Heridos/Acc","Fallecidos/1000 Acc"]
        vic_tbl = vic_tbl.sort_values("Total Víctimas",ascending=False).reset_index(drop=True)
        vic_tbl.index += 1
        st.dataframe(vic_tbl.style
            .background_gradient(subset=["Total Víctimas"],cmap="Blues")
            .background_gradient(subset=["Índ. Gravedad"],cmap="RdYlGn_r")
            .format({"Heridos":"{:,.0f}","Fallecidos":"{:,.0f}","Total Víctimas":"{:,.0f}",
                     "Índ. Gravedad":"{:.3f}","Heridos/Acc":"{:.3f}","Fallecidos/1000 Acc":"{:.2f}"}),
            use_container_width=True, height=420)

    with tab2:
        muni = d["muni"].copy()
        muni["municipio_full"] = muni["municipio"]+" ("+muni["entidad"]+")"
        col_v = st.selectbox("Ordenar por:", ["victimas_heridas","victimas_muertas","total_victimas","indice_gravedad"])
        min_a = st.slider("Accidentes mínimos:", 100, 5000, 500, 100)
        top_v = muni[muni["accidentes"]>=min_a].sort_values(col_v,ascending=False).head(20)

        fig3 = px.bar(top_v,x=col_v,y="municipio_full",orientation="h",
                      color=col_v,color_continuous_scale="Reds",
                      hover_data={"accidentes":True,"indice_gravedad":True})
        fig3.update_layout(**base_layout(height=540,coloraxis_showscale=False,
                           yaxis=dict(gridcolor="rgba(0,0,0,0)",tickfont_size=10),
                           title=dict(text=f"Top 20 por {col_v.replace('_',' ').title()}",font_size=13,x=0)))
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        # Índice de gravedad desglosado por tipo
        typ = d["type"].copy()
        fig4 = go.Figure()
        for col_n,clr,nm in [("victimas_heridas","#ffd166","Heridos"),("victimas_muertas","#ff4b4b","Fallecidos")]:
            fig4.add_trace(go.Bar(x=typ["tipo_accidente"],y=typ[col_n],name=nm,
                                  marker_color=clr,opacity=.85))
        fig4.update_layout(**base_layout(height=360,barmode="stack",xaxis_tickangle=-30,
                           title=dict(text="Víctimas por Tipo de Accidente",font_size=13,x=0)))
        st.plotly_chart(fig4, use_container_width=True)

        # Pirámide de gravedad
        clf = d["classif"].copy()
        total_vic = clf["total_victimas"].sum()
        for_,dam = clf[clf["clasificacion_accidente"]=="Fatal"].iloc[0], \
                   clf[clf["clasificacion_accidente"]=="Sólo daños"].iloc[0]
        nofatal = clf[clf["clasificacion_accidente"]=="No fatal"].iloc[0]

        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="kpi-value">{fmt(for_["victimas_muertas"])}</div>'
                        f'<div class="kpi-label">Fallecidos (Fatales)</div>'
                        f'<div class="kpi-sub">gravedad: {for_["indice_gravedad"]:.2f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-value">{fmt(nofatal["victimas_heridas"])}</div>'
                        f'<div class="kpi-label">Heridos (No Fatales)</div>'
                        f'<div class="kpi-sub">gravedad: {nofatal["indice_gravedad"]:.2f}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="kpi-value">{fmt(dam["accidentes"])}</div>'
                        f'<div class="kpi-label">Solo Daños Materiales</div>'
                        f'<div class="kpi-sub">sin víctimas</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="insight-box"><strong>Atropellamientos</strong> y <strong>caídas de pasajero</strong> concentran víctimas con alta gravedad. Los accidentes fatales, aunque representan solo el 1.3% del total, generan el índice de gravedad más alto (6.43 víctimas por accidente). La <strong>mayoría de accidentes (81.4%) son solo daños materiales</strong>.</div>', unsafe_allow_html=True)

    with tab4:
        zone = d["zone"].copy()
        if zone.empty:
            st.info("Ejecuta nuevamente el pipeline para generar accidents_by_zone.csv.")
        else:
            zone = zone.sort_values("accidentes", ascending=False)
            col1, col2 = st.columns(2)
            with col1:
                fig5 = px.bar(zone, x="zona", y="accidentes", color="indice_gravedad",
                              color_continuous_scale="RdYlGn_r",
                              text="accidentes",
                              hover_data={"victimas_heridas": True, "victimas_muertas": True})
                fig5.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig5.update_layout(**base_layout(height=360, coloraxis_showscale=False,
                                   title=dict(text="Accidentes por Zona", font_size=13, x=0)))
                st.plotly_chart(fig5, use_container_width=True)
            with col2:
                fig6 = go.Figure()
                fig6.add_trace(go.Bar(x=zone["zona"], y=zone["victimas_heridas"],
                                      name="Heridos", marker_color="#ffd166", opacity=.88))
                fig6.add_trace(go.Bar(x=zone["zona"], y=zone["victimas_muertas"],
                                      name="Fallecidos", marker_color="#ff4b4b", opacity=.88))
                fig6.update_layout(**base_layout(height=360, barmode="group",
                                   title=dict(text="Víctimas por Zona", font_size=13, x=0)))
                st.plotly_chart(fig6, use_container_width=True)

            zone_tbl = zone[["zona", "accidentes", "accidentes_con_heridos",
                             "accidentes_con_muertos", "victimas_heridas",
                             "victimas_muertas", "total_victimas",
                             "indice_gravedad"]].copy()
            zone_tbl.columns = ["Zona", "Accidentes", "Con Heridos", "Con Fallecidos",
                                "Víctimas Heridas", "Víctimas Muertas",
                                "Total Víctimas", "Índ. Gravedad"]
            st.dataframe(zone_tbl.style
                .background_gradient(subset=["Accidentes"], cmap="Blues")
                .background_gradient(subset=["Índ. Gravedad"], cmap="RdYlGn_r")
                .format({"Accidentes":"{:,.0f}", "Con Heridos":"{:,.0f}",
                         "Con Fallecidos":"{:,.0f}", "Víctimas Heridas":"{:,.0f}",
                         "Víctimas Muertas":"{:,.0f}", "Total Víctimas":"{:,.0f}",
                         "Índ. Gravedad":"{:.3f}"}),
                use_container_width=True, hide_index=True)

            top_zone = zone.loc[zone["accidentes"].idxmax()]
            severe_zone = zone.loc[zone["indice_gravedad"].idxmax()]
            st.markdown(
                f'<div class="insight-box">La zona con mayor volumen es <strong>{top_zone["zona"]}</strong> '
                f'con <strong>{fmt(top_zone["accidentes"])}</strong> accidentes. '
                f'La zona con mayor severidad relativa es <strong>{severe_zone["zona"]}</strong> '
                f'con índice <strong>{severe_zone["indice_gravedad"]:.3f}</strong>.</div>',
                unsafe_allow_html=True,
            )

#RAY VS PANDAS
elif section == "Ray vs Pandas":
    st.markdown('<h1 style="font-size:1.8rem;color:#f0f2f6;margin-bottom:4px;">¿Qué tan eficiente es Ray frente a Pandas secuencial?</h1>', unsafe_allow_html=True)

    metrics = d["metrics"].copy()
    quality = d["quality"].copy()

    # ── Datos reales del pipeline ─────────────────────────────────────────────
    ray_total_s   = metrics["total_pipeline_seconds"].iloc[0]     # 334.8s
    total_rows    = metrics["rows_read"].iloc[0]                   # 10,730,849
    ray_rows_s    = metrics["rows_per_second"].sum()               # total throughput
    cleaned_rows  = metrics["rows_cleaned"].sum()                  # 1,892,726
    n_workers     = len(metrics)                                   # 3

    # Pandas secuencial = suma de elapsed de cada nodo (trabajo que Ray paralelizó)
    # Cada worker procesó su partición: si fuera 1 nodo haría la suma total
    pandas_est_s  = metrics["elapsed_seconds"].sum()              # 864.8s (suma de los 3 workers)
    pandas_io_est = total_rows / 600                               # estimado I/O puro ~17,884s
    speedup_real  = pandas_est_s / ray_total_s                    # x2.58 (real medido)
    speedup_io    = n_workers * (metrics["elapsed_seconds"].max() / ray_total_s)  # teórico lineal

    st.markdown('<div class="section-title">Métricas del Pipeline Ray</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi_data = [
        (c1,"info",f"{ray_total_s:.1f}s","Tiempo Total Ray","pipeline completo"),
        (c2,"warning",f"{total_rows/1e6:.2f}M","Filas Leídas","todos los archivos ATUS"),
        (c3,"success",fmt(cleaned_rows),"Filas Procesadas","limpias y validadas"),
        (c4,"purple",f"×{speedup_real:.1f}","Speedup vs Secuencial","estimado real"),
        (c5,"danger",str(n_workers),"Nodos Worker","Ray paralelo"),
    ]
    for col,cls,val,lbl,sub in kpi_data:
        with col:
            st.markdown(f'<div class="kpi-value">{val}</div>'
                        f'<div class="kpi-label">{lbl}</div>'
                        f'<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Comparación de Tiempos: Ray vs Pandas Secuencial</div>', unsafe_allow_html=True)
    col1,col2 = st.columns(2)

    with col1:
        # Comparación de tiempos estimados
        scenarios = pd.DataFrame({
            "Escenario": ["Pandas\nSecuencial\n(I/O est.)", "Pandas\nSecuencial\n(Suma workers)", "Ray\nParalelo\n(Real)"],
            "Tiempo (s)": [pandas_io_est, pandas_est_s, ray_total_s],
            "Tipo": ["Estimado", "Estimado", "Real"],
        })
        fig = go.Figure()
        colors_bar = ["#ff6b6b","#ffd166","#06d6a0"]
        for i,(row) in scenarios.iterrows():
            fig.add_trace(go.Bar(
                x=[row["Escenario"]], y=[row["Tiempo (s)"]],
                name=row["Escenario"].replace("\n"," "),
                marker_color=colors_bar[i],opacity=.88,
                text=[f"{row['Tiempo (s)']:.0f}s"],textposition="outside",
            ))
        # Línea de referencia
        fig.add_hline(y=ray_total_s,line_dash="dash",line_color="#06d6a0",
                      annotation_text=f"Ray: {ray_total_s:.1f}s",annotation_position="right")
        fig.update_layout(**base_layout(height=380,showlegend=False,
                          yaxis_title="Tiempo (segundos)",
                          title=dict(text="Tiempo de Procesamiento Total",font_size=13,x=0)))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Speedup por escenario
        speedups = pd.DataFrame({
            "Escenario": ["vs I/O Pandas\n(est. 600 rows/s)", f"vs Suma\nWorkers\nSecuencial"],
            "Speedup": [speedup_io, speedup_real],
        })
        fig2 = go.Figure(go.Bar(
            x=speedups["Escenario"], y=speedups["Speedup"],
            marker_color=["#a78bfa","#4b8fff"],opacity=.88,
            text=[f"×{s:.1f}" for s in speedups["Speedup"]],
            textposition="outside",textfont_size=18,
        ))
        fig2.add_hline(y=n_workers,line_dash="dot",line_color="#ffd166",
                       annotation_text=f"Speedup lineal teórico (×{n_workers})",annotation_position="right")
        fig2.update_layout(**base_layout(height=380,
                           yaxis_title="Factor de aceleración (×)",
                           title=dict(text="Speedup de Ray vs Pandas Secuencial",font_size=13,x=0)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-title">Rendimiento por Nodo Worker</div>', unsafe_allow_html=True)
    col3,col4 = st.columns(2)

    with col3:
        fig3 = go.Figure()
        worker_labels = [f"Worker {i+1}\n{m}" for i,m in enumerate(["A-C","D-M","N-Z"])]
        fig3.add_trace(go.Bar(x=worker_labels,y=metrics["rows_cleaned"],
                              name="Filas procesadas",marker_color="#4b8fff",opacity=.88,
                              text=metrics["rows_cleaned"].apply(lambda x: f"{x:,}"),
                              textposition="outside"))
        fig3.add_trace(go.Scatter(x=worker_labels,y=metrics["elapsed_seconds"],
                                  name="Tiempo (s)",mode="lines+markers",
                                  line=dict(color="#ffd166",width=2.5),marker_size=10,yaxis="y2"))
        fig3.update_layout(**base_layout(height=340,
                           yaxis_title="Filas procesadas",
                           yaxis2=dict(overlaying="y",side="right",title="Segundos",
                                       gridcolor="rgba(0,0,0,0)"),
                           title=dict(text="Carga y Tiempo por Worker",font_size=13,x=0)))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = go.Figure(go.Bar(
            x=worker_labels, y=metrics["rows_per_second"],
            marker=dict(color=metrics["rows_per_second"],colorscale="Viridis"),
            text=metrics["rows_per_second"].apply(lambda x: f"{x:,.0f}/s"),
            textposition="outside", opacity=.88,
        ))
        fig4.update_layout(**base_layout(height=340,
                           yaxis_title="Filas procesadas por segundo",
                           title=dict(text="Throughput por Nodo Worker",font_size=13,x=0),
                           coloraxis_showscale=False))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">Tiempo de Procesamiento por Archivo (Workers)</div>', unsafe_allow_html=True)
    proc_files2 = quality[quality["rows_cleaned"]>0][
        ["worker_node","fuente_archivo","año","rows_cleaned","elapsed_seconds"]].copy()
    proc_files2["rows_per_sec"] = (proc_files2["rows_cleaned"]/proc_files2["elapsed_seconds"]).round(0)
    proc_files2["worker_label"] = proc_files2["worker_node"].str.replace("worker_node_","W")
    fig5 = px.bar(proc_files2.sort_values("año"),
                  x="año",y="elapsed_seconds",color="worker_label",
                  barmode="group",
                  color_discrete_map={"W1_a_c":"#4b8fff","W2_d_m":"#ffd166","W3_n_z":"#06d6a0"},
                  hover_data={"rows_cleaned":True,"rows_per_sec":True,"fuente_archivo":True})
    fig5.update_layout(**base_layout(height=340,
                       xaxis_title="Año del archivo procesado",yaxis_title="Segundos",
                       title=dict(text="Tiempo por Archivo y Worker (archivos procesados con datos válidos)",font_size=12,x=0)))
    st.plotly_chart(fig5, use_container_width=True)

    # Tabla de métricas
    st.markdown('<div class="section-title">Tabla de Métricas del Pipeline</div>', unsafe_allow_html=True)
    metrics_disp = metrics.copy()
    metrics_disp.columns = ["Nodo","Filas Leídas","Filas Asignadas","Filas Limpias",
                             "Tiempo Worker (s)","Motor","Tiempo Total (s)","Filas/seg"]
    total_row = pd.DataFrame([{
        "Nodo":" TOTAL",
        "Filas Leídas":metrics_disp["Filas Leídas"].iloc[0],
        "Filas Asignadas":metrics_disp["Filas Asignadas"].sum(),
        "Filas Limpias":metrics_disp["Filas Limpias"].sum(),
        "Tiempo Worker (s)":"—",
        "Motor":"Ray (3 nodos)",
        "Tiempo Total (s)":metrics_disp["Tiempo Total (s)"].iloc[0],
        "Filas/seg":metrics_disp["Filas/seg"].sum(),
    }])
    metrics_disp = pd.concat([metrics_disp,total_row],ignore_index=True)
    st.dataframe(metrics_disp, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="insight-box">
    <strong>Conclusión del benchmark Ray vs Pandas:</strong><br><br>
    Ray procesó <strong>10,730,849 filas</strong> en <strong>{ray_total_s:.0f} segundos</strong> (~5.6 min) usando 3 nodos en paralelo.<br>
    La misma carga en un solo nodo secuencial tomaría <strong>{pandas_est_s:.0f}s</strong> (~14.4 min), que es la suma real del trabajo de cada worker.<br>
    El <strong>speedup real es ×{speedup_real:.2f}</strong> (teórico lineal máximo = ×{n_workers}). La eficiencia paralela es del <strong>{speedup_real/n_workers*100:.0f}%</strong>.<br>
    El nodo W3 (apellidos N-Z) procesó más filas ({metrics['rows_cleaned'].iloc[2]:,}) y más tiempo ({metrics['elapsed_seconds'].iloc[2]:.1f}s), evidenciando <strong>desbalance de carga</strong> por distribución alfabética desigual.<br>
    Ray permite escalar horizontalmente: con 6 nodos el speedup teórico sería ×5-6, reduciendo el tiempo a ~<strong>2-3 minutos</strong>.
    </div>""", unsafe_allow_html=True)

#Footer
st.markdown("""
<div class="footer">
  Proyecto Parcial 3 · Cómputo Paralelo y Distribuido<br>
  Laura Cecilia Holguín Campos, Ana Rebeca Moreno Reza

</div>
""", unsafe_allow_html=True)
