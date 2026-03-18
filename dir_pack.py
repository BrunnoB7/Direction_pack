import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from scipy.optimize import root_scalar


# ----------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ----------------------------------------------------------

st.set_page_config(
    page_title="Horizontal Well Optimizer",
    page_icon="🛢️",
    layout="wide"
)

st.image('logo_syng.png')
st.sidebar.image('logo_syngular_png.png', width=225)

# ----------------------------------------------------------
# ESTILO VISUAL (deixa mais profissional)
# ----------------------------------------------------------

st.markdown("""
<style>

.main-title {
    font-size:28px;
    font-weight:600;
}

.block-container {
    padding-top:2rem;
}

.metric-card {
    background-color:#f5f5f5;
    padding:20px;
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# HEADER
# ----------------------------------------------------------

st.markdown('### Otimização de Trecho Horizontal')

st.markdown(
"""
Para um conjunto de propriedades do reservatório, o software analisa a distribuição de pressão ao longo da seção 
horizontal do poço. A ferramenta permite realizar análises de sensibilidade do comprimento do trecho horizontal e do 
diâmetro do poço, possibilitando a estimativa do comprimento horizontal ótimo.
"""
)

st.divider()

# ----------------------------------------------------------
# SIDEBAR - PARÂMETROS DO USUÁRIO
# ----------------------------------------------------------

st.sidebar.header("Parâmetros de Entrada")

# valores iniciais
if "slide_ch" not in st.session_state:
    st.session_state.slide_ch = 500.0

if "ch" not in st.session_state:
    st.session_state.ch = 500.0


# sincroniza quando o slider muda
def update_from_slider():
    st.session_state.ch = st.session_state.slide_ch


# sincroniza quando o number_input muda
def update_from_input():
    st.session_state.slide_ch = st.session_state.ch


liner_length = st.sidebar.slider(
    "Comprimento da seção horizontal (m)",
    min_value=100.0,
    max_value=2000.0,
    step=0.1,
    key="slide_ch",
    on_change=update_from_slider
)

st.sidebar.number_input(
    "Comprimento da seção horizontal (m)",
    min_value=100.0,
    max_value=2000.0,
    step=0.1,
    key="ch",
    on_change=update_from_input
)

# liner_length = st.sidebar.slider(
#     "Horizontal Section Length (m)",
#     min_value=100.0,
#     max_value=2000.0,
#     step=0.1,
#     value=st.session_state.ch,
#     key='slide_ch'
# )

# st.sidebar.number_input('Comprimento da seção horizontal', min_value=50.0, max_value=2000.0, key='ch', step=0.1)

diameters = {
    '12 1/4" x 9 5/8"': 12.25/39.37,
    '8 1/2" x 7"': 0.1778,
    '6 1/8" x 5"': 0.127,
    '6 1/8" x 4 3/4"': 0.12065
}

liner_diameter = st.sidebar.selectbox(
    "Diâmetro do trecho horizontal (in)",
    ['12 1/4" x 9 5/8"', '8 1/2" x 7"', '6 1/8" x 5"', '6 1/8" x 4 3/4"']
)

st.sidebar.markdown("---")


# ----------------------------------------------------------
# FUNÇÃO DE CÁLCULO (placeholder)
# ----------------------------------------------------------
if 'flow_rate' not in st.session_state:
    st.session_state.flow_rate = 0.011199996916908863
# flow_rate = 0.000469999999949006  # m3/s
# flow_s = flow_rate/liner_length
flow_s = 5 * 10**-7
screen_hole_d = 0.01  # m
dis = 0.9
perm = 1 * 10**-13  # m2
rw = 0.08  # m
visc = 2  # Pa*s
dens = 870  # kg/m3
Pres = 5 * 10**6  # Pa
segs = 200

#Calculo do coeficiente de atrito
vel = (4 * st.session_state.flow_rate)/(np.pi * diameters[liner_diameter]**2)
rey = (dens * diameters[liner_diameter] * vel)/visc
f = 0.0791/(rey**0.25)


df = pd.DataFrame()
#  Montagem da tabela
df['Index'] = np.arange(1, 201)
df['x_i'] = (df['Index'] - 1) * (liner_length/segs)


def equation(flow_rate=st.session_state.flow_rate):
    p1 = Pres + (flow_rate - flow_s * liner_length) / (4 * np.pi * rw * perm) * visc
    p2 = (3.24 * f * dens) / (3 * flow_s * diameters[liner_diameter] ** 5)
    p3 = (flow_rate - flow_s * df['x_i']) ** 3 - (flow_rate - flow_s * liner_length) ** 3
    p4 = p1 - p2*p3
    return p4[0]


def goal(flow_rate=st.session_state.flow_rate):
    return equation(flow_rate) - 4999920


if st.sidebar.button("Atualizar simulação"):
    solution = root_scalar(goal, bracket=[0, 1])
    st.session_state.flow_rate = solution.root
    st.rerun()


df['Q(x_i)'] = st.session_state.flow_rate - flow_s * df['x_i']

# Partição do calculo de pxi
p1 = Pres + (st.session_state.flow_rate - flow_s*liner_length)/(4 * np.pi * rw * perm) * visc
p2 = (3.24 * f * dens)/(3 * flow_s * diameters[liner_diameter]**5)
p3 = (st.session_state.flow_rate - flow_s*df['x_i'])**3 - (st.session_state.flow_rate - flow_s*liner_length)**3

df['P(x_i)'] = p1 - p2*p3
df['Delta_P'] = Pres - df['P(x_i)']
df['Q_perf'] = dis * screen_hole_d**2 * np.sqrt(df['Delta_P']/(0.81*dens))
df['N(x_i)'] = flow_s / df['Q_perf']
df['Nº furos'] = df['N(x_i)'] * df['x_i']
df['qi'] = df['N(x_i)']*df['Q_perf']*(liner_length/segs)

df = df.fillna(0)


# ----------------------------------------------------------
# CARDS DE RESULTADOS
# ----------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Comprimento Horizontal",
        value=f"{liner_length:.2f} m"
    )

with col2:
    st.metric(
        label="Diâmetro trecho horizontal",
        value=f"{liner_diameter} "
    )

with col3:
    production = sum(df['qi'] * 86400 * 6.29)
    st.metric(
        label="Produção diária",
        value=f"{production:.0f} bbl/d"
    )

st.divider()

# ----------------------------------------------------------
# GRÁFICO
# ----------------------------------------------------------

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df['x_i'],
        y=df['P(x_i)'],
        mode="lines",
        name="Pressão ao longo do trecho horizontal",
        line=dict(width=4)
    )
)

fig.add_trace(
    go.Scatter(
        x=df['x_i'],
        y=[Pres]*len(df['x_i']),
        mode="lines",
        name="Pressão do reservatório",
        line=dict(dash="dash")
    )
)

fig.update_layout(
    title="Distribuição de pressão ao  longo do trecho horizontal",
    xaxis_title="Distancia ao longo do trecho horizontal (m)",
    yaxis_title="Pressão (Pa)",
    template="plotly_white",
    height=600
)
fig.update_xaxes(dtick=100)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------
# TABELA OPCIONAL (debug)
# ----------------------------------------------------------

with st.expander("Dados calculados"):

    st.dataframe(df, hide_index=True)
