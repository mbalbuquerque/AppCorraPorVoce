import streamlit as st
import mysql.connector
import pandas as pd

st.sidebar.image("logocorraporvc.png", use_container_width=True)
# Estilização Premium com sua paleta

# No topo do código, logo após st.set_page_config

st.markdown(f"""
    <style>
    /* Cor de fundo principal */
    .stApp {{
        background-color: black;
    }}
    
    /* Menu Lateral */
    [data-testid="stSidebar"] {{
        background-color: black;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    /* Botões Customizados */
    .stButton>button {{
        background-color: #174DEB;
        color: #000;
        border-radius: 8px;
        border: 1px solid #174DEB;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: #174DEB;
        color: black;
    }}
    /* Títulos */
    h1, h2, h3 {{
        color: #174DEB;
    }}
    </style>
    """, unsafe_allow_html=True)


# 1. FUNÇÃO DE CONEXÃO (Ajuste sua senha se necessário)
def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="teste", # Se no seu Workbench tiver senha, coloque aqui
        database="corra_por_voce"
    )

# Inicializa a conexão
conn = conectar()

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Corra Por Você", layout="wide")
st.title("🏃 Dashboard Corra Por Você")

# 3. MENU LATERAL
menu = st.sidebar.selectbox("Navegação", 
    ["Resumo de Treinos", "Cadastrar Treino", "Gerenciar Atletas"])

# --- FUNCIONALIDADE: GERENCIAR ATLETAS ---
if menu == "Gerenciar Atletas":
    st.header("👤 Gerenciar Atletas")
    
    # Formulário de Cadastro
    with st.form("form_novo_atleta", clear_on_submit=True):
        nome = st.text_input("Nome do Atleta")
        altura = st.number_input("Altura (m)", min_value=1.0, value=1.70, step=0.01)
        btn_cadastrar = st.form_submit_button("Cadastrar")
        
        if btn_cadastrar:
            if nome:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (nome, altura) VALUES (%s, %s)", (nome, altura))
                conn.commit()
                st.success(f"Atleta {nome} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha o nome.")

    # Listagem de Atletas
    st.subheader("Atletas no Sistema")
    df_usuarios = pd.read_sql("SELECT id, nome, altura FROM usuarios", conn)
    st.dataframe(df_usuarios, use_container_width=True)

# --- FUNCIONALIDADE: CADASTRAR TREINO ---
elif menu == "Cadastrar Treino":
    st.header("📝 Registrar Novo Treino")
    
    # Busca atletas para o seletor
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios")
    usuarios_dict = {nome: id for id, nome in cursor.fetchall()}
    
    if not usuarios_dict:
        st.warning("Nenhum atleta cadastrado. Vá em 'Gerenciar Atletas' primeiro.")
    else:
        with st.form("form_treino"):
            atleta_nome = st.selectbox("Selecione o Atleta", list(usuarios_dict.keys()))
            tipo = st.selectbox("Tipo de Atividade", ["Corrida", "Caminhada"])
            distancia = st.number_input("Distância (km)", min_value=0.1, step=0.1)
            duracao = st.text_input("Duração (HH:MM:SS)", value="00:30:00")
            btn_treino = st.form_submit_button("Salvar Treino")
            
            if btn_treino:
                id_atleta = usuarios_dict[atleta_nome]
                cursor.execute(
                    "INSERT INTO atividades (usuario_id, tipo, distancia, duracao) VALUES (%s, %s, %s, %s)",
                    (id_atleta, tipo, distancia, duracao)
                )
                conn.commit()
                st.success(f"Treino de {atleta_nome} registrado!")

# --- FUNCIONALIDADE: RESUMO ---
elif menu == "Resumo de Treinos":
    st.header("📊 Performance Geral")
    try:
        df_resumo = pd.read_sql("SELECT * FROM v_resumo_treinos", conn)
        if df_resumo.empty:
            st.info("Ainda não há treinos registrados para exibir no resumo.")
        else:
            st.table(df_resumo)
    except:
        st.error("Erro ao carregar o resumo. Verifique se a View 'v_resumo_treinos' existe no MySQL.")
        
# --- FUNCIONALIDADE: EVOLUÇÃO DE PESO ---
elif menu == "Evolução de Peso":
    st.header("⚖️ Evolução de Peso e IMC")
    
    # 1. Formulário para nova pesagem
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios")
    usuarios_dict = {nome: id for id, nome in cursor.fetchall()}
    
    with st.form("form_peso"):
        atleta_peso = st.selectbox("Selecione o Atleta", list(usuarios_dict.keys()))
        peso_valor = st.number_input("Peso Atual (kg)", min_value=10.0, step=0.1)
        btn_peso = st.form_submit_button("Registrar Peso")
        
        if btn_peso:
            id_u = usuarios_dict[atleta_peso]
            cursor.execute("INSERT INTO medicoes_peso (usuario_id, peso) VALUES (%s, %s)", (id_u, peso_valor))
            conn.commit()
            st.success(f"Peso de {atleta_peso} registrado!")
            st.rerun()

    # 2. Visualização do Histórico e IMC
    st.divider()
    st.subheader("Histórico de Saúde")
    try:
        # Busca os dados da View que criamos no Workbench
        df_imc = pd.read_sql("SELECT * FROM v_historico_imc", conn)
        if not df_imc.empty:
            st.line_chart(df_imc.set_index('data_medicao')['peso']) # Gráfico de linha do peso
            st.dataframe(df_imc, use_container_width=True)
        else:
            st.info("Nenhuma medição encontrada.")
    except:
        st.error("Erro ao carregar histórico. Verifique se a View 'v_historico_imc' existe.")

# --- BOA PRÁTICA: FECHAR CONEXÃO ---
# O ideal no Streamlit é fechar apenas se você não for usar mais a conexão no script
# No entanto, como o Streamlit roda o script do topo toda hora, 
# deixar o MySQL gerenciar o timeout costuma ser mais estável.

# --- FINALIZAÇÃO E RODAPÉ ---
st.sidebar.divider()
st.sidebar.write(f"🟢 **Status:** Conectado ao MySQL")

# Rodapé com a paleta aplicada
st.markdown("---")
st.caption("🚀 **Dashboard Corra Por Você** | Foco, Saúde e Performance")

# Boa prática: fechar o cursor se ele existir
try:
    if 'cursor' in locals():
        cursor.close()
except:
    pass