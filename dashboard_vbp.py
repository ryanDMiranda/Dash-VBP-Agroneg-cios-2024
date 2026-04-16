import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback
import numpy as np
import os

# ──────────────────────────────────────────────
# 1. CARREGAMENTO E LIMPEZA DOS DADOS
# ──────────────────────────────────────────────

# Verificação do arquivo CSV
csv_path = "VBP_Tabela.csv"
if not os.path.exists(csv_path):
    print(f"ERRO: O arquivo '{csv_path}' não foi encontrado no diretório atual.")
    # Criando um DataFrame vazio ou de exemplo para não quebrar o app totalmente se o arquivo sumir
    df_raw = pd.DataFrame(columns=["Municipio", "Regiao", "VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"])
else:
    try:
        df_raw = pd.read_csv(
            csv_path,
            encoding="utf-16-le",
            sep="\t",
            skiprows=2,
            header=0,
        )
        df_raw.columns = ["Municipio", "Regiao", "VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"]
    except Exception as e:
        print(f"Erro ao ler o CSV: {e}")
        df_raw = pd.DataFrame(columns=["Municipio", "Regiao", "VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"])

def parse_br(val):
    try:
        if pd.isna(val): return 0.0
        return float(str(val).replace(".", "").replace(",", "."))
    except:
        return 0.0

for col in ["VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"]:
    if col in df_raw.columns:
        df_raw[col] = df_raw[col].apply(parse_br)

if not df_raw.empty:
    estado_row = df_raw.iloc[0]
    df = df_raw.iloc[1:].copy().reset_index(drop=True)
    df.dropna(subset=["VBP_Total"], inplace=True)

    total_vbp      = estado_row["VBP_Total"]
    total_agri     = estado_row["VBP_Agricultura"]
    total_flor     = estado_row["VBP_Florestais"]
    total_pec      = estado_row["VBP_Pecuaria"]
else:
    df = pd.DataFrame(columns=["Municipio", "Regiao", "VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"])
    total_vbp = total_agri = total_flor = total_pec = 0

# Métricas por região
if not df.empty:
    df_regiao = (
        df.groupby("Regiao")[["VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"]]
        .sum()
        .sort_values("VBP_Total", ascending=False)
        .reset_index()
    )
    regioes = sorted(df["Regiao"].unique())
else:
    df_regiao = pd.DataFrame(columns=["Regiao", "VBP_Total", "VBP_Agricultura", "VBP_Florestais", "VBP_Pecuaria"])
    regioes = []

# ──────────────────────────────────────────────
# 2. PALETA E TEMA
# ──────────────────────────────────────────────
VERDE_DARK  = "#0d2b1a"
VERDE_MED   = "#14532d"
VERDE_ACC   = "#22c55e"
VERDE_LIGHT = "#86efac"
GOLD        = "#f59e0b"
TERRA       = "#92400e"
BEIGE       = "#fef9ef"
TEXTO       = "#f0fdf4"
CARD_BG     = "rgba(20,83,45,0.45)"
PLOT_BG     = "rgba(0,0,0,0)"
GRID_CLR    = "rgba(134,239,172,0.10)"

TEMPLATE_LAYOUT = dict(
    paper_bgcolor=PLOT_BG,
    plot_bgcolor=PLOT_BG,
    font=dict(family="DM Sans, sans-serif", color=TEXTO),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    colorway=[VERDE_ACC, GOLD, "#38bdf8", "#f87171", "#c084fc", "#fb923c"],
)

def apply_template(fig):
    fig.update_layout(**TEMPLATE_LAYOUT)
    fig.update_xaxes(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=dict(size=10))
    return fig

def fmt_bi(v):
    if v >= 1e9:
        return f"R$ {v/1e9:.2f} bi"
    elif v >= 1e6:
        return f"R$ {v/1e6:.1f} mi"
    return f"R$ {v:,.0f}"

# ──────────────────────────────────────────────
# 3. FIGURAS PRÉ-CALCULADAS
# ──────────────────────────────────────────────
def fig_donut():
    labels = ["Agricultura", "Florestais", "Pecuária"]
    values = [total_agri, total_flor, total_pec]
    colors = [VERDE_ACC, GOLD, "#38bdf8"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.62,
        marker=dict(colors=colors, line=dict(color=VERDE_DARK, width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color=TEXTO),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{fmt_bi(total_vbp)}</b>",
        x=0.5, y=0.55, showarrow=False,
        font=dict(size=14, color=VERDE_ACC),
        xanchor="center",
    )
    fig.add_annotation(
        text="VBP Total",
        x=0.5, y=0.42, showarrow=False,
        font=dict(size=11, color=TEXTO),
        xanchor="center",
    )
    fig.update_layout(**TEMPLATE_LAYOUT, title="Composição do VBP Estadual")
    return fig


def fig_top_municipios(n=15):
    if df.empty: return go.Figure(layout=TEMPLATE_LAYOUT)
    top = df.nlargest(n, "VBP_Total").sort_values("VBP_Total")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["Municipio"],
        x=top["VBP_Pecuaria"],
        name="Pecuária",
        orientation="h",
        marker=dict(color="#38bdf8"),
        hovertemplate="%{y}<br>Pecuária: R$ %{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=top["Municipio"],
        x=top["VBP_Florestais"],
        name="Florestais",
        orientation="h",
        marker=dict(color=GOLD),
        hovertemplate="%{y}<br>Florestais: R$ %{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=top["Municipio"],
        x=top["VBP_Agricultura"],
        name="Agricultura",
        orientation="h",
        marker=dict(color=VERDE_ACC),
        hovertemplate="%{y}<br>Agricultura: R$ %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **TEMPLATE_LAYOUT,
        barmode="stack",
        title=f"Top {n} Municípios por VBP Total",
        height=480,
        xaxis=dict(tickformat=",.0f"),
    )
    return apply_template(fig)


def fig_treemap():
    if df.empty: return go.Figure(layout=TEMPLATE_LAYOUT)
    fig = px.treemap(
        df,
        path=["Regiao", "Municipio"],
        values="VBP_Total",
        color="VBP_Total",
        color_continuous_scale=["#0d2b1a", VERDE_MED, VERDE_ACC, GOLD],
        hover_data={"VBP_Total": ":,.0f"},
        title="Distribuição Geográfica do VBP (Região → Município)",
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>VBP: R$ %{value:,.0f}<extra></extra>",
        textfont=dict(size=11),
    )
    fig.update_layout(**TEMPLATE_LAYOUT, height=440, coloraxis_showscale=False)
    return fig


def fig_scatter():
    if df.empty: return go.Figure(layout=TEMPLATE_LAYOUT)
    fig = px.scatter(
        df,
        x="VBP_Agricultura",
        y="VBP_Pecuaria",
        size="VBP_Total",
        color="Regiao",
        hover_name="Municipio",
        title="Agricultura × Pecuária por Município",
        labels={"VBP_Agricultura": "Agricultura (R$)", "VBP_Pecuaria": "Pecuária (R$)"},
        size_max=40,
    )
    fig.update_layout(**TEMPLATE_LAYOUT, height=420)
    fig.update_xaxes(gridcolor=GRID_CLR, tickformat=",.0f")
    fig.update_yaxes(gridcolor=GRID_CLR, tickformat=",.0f")
    return fig


def fig_regiao(selected_regiao=None):
    if df_regiao.empty: return go.Figure(layout=TEMPLATE_LAYOUT)
    dta = df_regiao.copy()
    colors = [VERDE_ACC if (selected_regiao is None or r == selected_regiao) else "rgba(34,197,94,0.25)"
              for r in dta["Regiao"]]
    fig = go.Figure(go.Bar(
        x=dta["VBP_Total"],
        y=dta["Regiao"],
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>VBP Total: R$ %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **TEMPLATE_LAYOUT,
        title="VBP Total por Região (RGI)",
        height=520,
        xaxis=dict(tickformat=",.0f"),
        yaxis=dict(autorange="reversed"),
    )
    return apply_template(fig)


def fig_regiao_detail(regiao):
    if df.empty: return go.Figure(layout=TEMPLATE_LAYOUT)
    sub = df[df["Regiao"] == regiao].nlargest(12, "VBP_Total")
    fig = go.Figure()
    for col, color, name in [
        ("VBP_Agricultura", VERDE_ACC, "Agricultura"),
        ("VBP_Florestais", GOLD, "Florestais"),
        ("VBP_Pecuaria", "#38bdf8", "Pecuária"),
    ]:
        fig.add_trace(go.Bar(
            x=sub["Municipio"], y=sub[col],
            name=name, marker=dict(color=color),
            hovertemplate=f"<b>%{{x}}</b><br>{name}: R$ %{{y:,.0f}}<extra></extra>",
        ))
    fig.update_layout(
        **TEMPLATE_LAYOUT,
        barmode="group",
        title=f"Municípios — {regiao}",
        height=350,
        yaxis=dict(tickformat=",.0f"),
    )
    return apply_template(fig)


# ──────────────────────────────────────────────
# 4. LAYOUT DO APP
# ──────────────────────────────────────────────
def kpi_card(title, value, sub="2024", color=VERDE_ACC):
    return html.Div([
        html.P(title, style={"margin": "0 0 4px 0", "fontSize": "12px", "color": "rgba(240,253,244,0.65)", "textTransform": "uppercase", "letterSpacing": "1px"}),
        html.H3(fmt_bi(value), style={"margin": "0 0 2px 0", "fontSize": "22px", "color": color, "fontWeight": "700"}),
        html.Span(sub, style={"fontSize": "11px", "color": "rgba(240,253,244,0.4)"}),
    ], style={
        "background": CARD_BG,
        "border": f"1px solid {color}30",
        "borderRadius": "12px",
        "padding": "18px 20px",
        "flex": "1",
        "backdropFilter": "blur(8px)",
        "boxShadow": f"0 0 24px {color}18",
        "minWidth": "180px",
    })


app = dash.Dash(__name__, title="VBP Paraná — Dashboard")

app.layout = html.Div([

    # ── FONTS ──
    html.Link(rel="preconnect", href="https://fonts.googleapis.com"),
    html.Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@700&display=swap"),

    # ── HEADER ──
    html.Div([
        html.Div([
            html.Span("🌱", style={"fontSize": "28px", "marginRight": "12px"}),
            html.Div([
                html.H1("VBP Paraná", style={"margin": "0", "fontSize": "26px", "fontFamily": "'Playfair Display', serif", "color": VERDE_ACC}),
                html.P("Valor Bruto da Produção Agropecuária · 2024", style={"margin": "0", "fontSize": "12px", "color": "rgba(240,253,244,0.5)"}),
            ]),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            html.Span("Paraná", style={"background": f"{VERDE_ACC}22", "color": VERDE_ACC, "padding": "4px 12px", "borderRadius": "20px", "fontSize": "12px", "border": f"1px solid {VERDE_ACC}44"}),
        ]),
    ], style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": "20px 32px", "borderBottom": f"1px solid {VERDE_ACC}22",
        "background": f"linear-gradient(90deg, {VERDE_DARK} 0%, #0f3d22 100%)",
    }),

    # ── MAIN ──
    html.Div([

        # KPI CARDS
        html.Div([
            kpi_card("VBP Total",      total_vbp,  color=VERDE_ACC),
            kpi_card("Agricultura",    total_agri, color="#86efac"),
            kpi_card("Pecuária",       total_pec,  color="#38bdf8"),
            kpi_card("Florestais",     total_flor, color=GOLD),
            kpi_card("Municípios",     399,        sub="municípios analisados", color="#c084fc"),
        ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "24px"}),

        # ROW 1 — Donut + Top Municípios
        html.Div([
            html.Div(dcc.Graph(figure=fig_donut(), config={"displayModeBar": False}),
                     style={"flex": "0 0 320px", "background": CARD_BG, "borderRadius": "12px", "padding": "8px", "border": f"1px solid {VERDE_ACC}20"}),
            html.Div(dcc.Graph(figure=fig_top_municipios(), config={"displayModeBar": False}),
                     style={"flex": "1", "background": CARD_BG, "borderRadius": "12px", "padding": "8px", "border": f"1px solid {VERDE_ACC}20"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}),

        # ROW 2 — Treemap + Scatter
        html.Div([
            html.Div(dcc.Graph(figure=fig_treemap(), config={"displayModeBar": False}),
                     style={"flex": "1", "background": CARD_BG, "borderRadius": "12px", "padding": "8px", "border": f"1px solid {VERDE_ACC}20", "minWidth": "340px"}),
            html.Div(dcc.Graph(figure=fig_scatter(), config={"displayModeBar": False}),
                     style={"flex": "1", "background": CARD_BG, "borderRadius": "12px", "padding": "8px", "border": f"1px solid {VERDE_ACC}20", "minWidth": "340px"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "24px", "flexWrap": "wrap"}),

        # ROW 3 — Regiões (interativo)
        html.Div([
            html.P("Clique em uma região para ver os municípios", style={"margin": "0 0 12px 0", "fontSize": "12px", "color": "rgba(240,253,244,0.5)"}),
            html.Div([
                html.Div(dcc.Graph(id="bar-regioes", figure=fig_regiao(), config={"displayModeBar": False}),
                         style={"flex": "1", "minWidth": "300px"}),
                html.Div(dcc.Graph(id="bar-regiao-detail", figure=go.Figure(layout={**TEMPLATE_LAYOUT, "title": "← Selecione uma Região", "height": 350}),
                                   config={"displayModeBar": False}),
                         style={"flex": "1.4", "minWidth": "300px"}),
            ], style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),
        ], style={"background": CARD_BG, "borderRadius": "12px", "padding": "20px", "border": f"1px solid {VERDE_ACC}20", "marginBottom": "24px"}),

        # FOOTER
        html.P("Fonte: MAPA — Ministério da Agricultura, Pecuária e Abastecimento · VBP 2024",
               style={"textAlign": "center", "fontSize": "11px", "color": "rgba(240,253,244,0.3)", "marginTop": "8px"}),

    ], style={"padding": "24px 32px", "maxWidth": "1400px", "margin": "0 auto"}),

], style={
    "minHeight": "100vh",
    "background": f"radial-gradient(ellipse at 20% 20%, #0d3320 0%, {VERDE_DARK} 60%, #050d08 100%)",
    "fontFamily": "'DM Sans', sans-serif",
    "color": TEXTO,
})


# ──────────────────────────────────────────────
# 5. CALLBACKS
# ──────────────────────────────────────────────
@app.callback(
    Output("bar-regiao-detail", "figure"),
    Output("bar-regioes", "figure"),
    Input("bar-regioes", "clickData"),
)
def update_detail(click_data):
    if click_data is None:
        return (
            go.Figure(layout={**TEMPLATE_LAYOUT, "title": "← Selecione uma Região", "height": 350}),
            fig_regiao()
        )
    regiao = click_data["points"][0]["y"]
    return fig_regiao_detail(regiao), fig_regiao(regiao)


if __name__ == "__main__":
    print("\n🌱  Dashboard VBP Paraná iniciando...")
    print("   Acesse: http://127.0.0.1:8050\n")
    app.run(debug=False, port=8050)
