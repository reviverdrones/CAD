import streamlit as st
from datetime import date, timedelta

# --- FUNÇÃO DE RECARREGAMENTO COMPATÍVEL ---
def force_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# --- CÁLCULO DE DATAS SEM DEPENDÊNCIA EXTERNA ---
def calcular_intersticio(data_inicio, data_fim):
    """Calcula anos e meses entre duas datas usando Python nativo"""
    anos = data_fim.year - data_inicio.year
    meses = data_fim.month - data_inicio.month
    dias = data_fim.day - data_inicio.day

    if dias < 0:
        meses -= 1
        # Aproximação simples de dias para evitar erro de calendário
        dias += 30 
    
    if meses < 0:
        anos -= 1
        meses += 12
        
    return anos, meses, dias

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(page_title="CAD EMHUR - Gestão Jurídica", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F9FAFB; }
    h1, h2, h3 { color: #1E3A8A; font-family: sans-serif; }
    .stButton>button {
        background-color: #1E3A8A; color: white; border-radius: 10px; border: none;
        padding: 10px 24px; font-weight: bold;
    }
    .metric-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 5px solid #1E3A8A; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADO ---
if 'cursos' not in st.session_state:
    st.session_state.cursos = []
if 'analise_realizada' not in st.session_state:
    st.session_state.analise_realizada = False
if 'dados_parecer' not in st.session_state:
    st.session_state.dados_parecer = {}
if 'resultado_analise' not in st.session_state:
    st.session_state.resultado_analise = {}

# --- FUNÇÕES DE LÓGICA JURÍDICA ---

def calcular_pontos(horas, relacao):
    direta = (relacao == 'DIRETA')
    if horas < 4: return 0
    if horas <= 20: return 5 if direta else 2
    if horas <= 40: return 10 if direta else 5
    if horas <= 60: return 15 if direta else 10
    if horas <= 80: return 20 if direta else 15
    return 25 if direta else 20

def proxima_classe(classe_atual):
    if not classe_atual or len(classe_atual) > 1: return "XX"
    try:
        char_code = ord(classe_atual.upper())
        return chr(char_code + 1)
    except:
        return "XX"

def gerar_parecer(dados, resultado):
    # Texto do relatório
    texto = (f"Empresa de Desenvolvimento Urbano e Habitacional - EMHUR\n"
             f"Comissão de Avaliação de Desempenho - CAD\n\n"
             f"Parecer nº {dados.get('num', '')}\nNUP: {dados.get('nup', '')}\n"
             f"Requerente: {dados.get('nome', '').upper()}\n"
             f"Assunto: {dados.get('modalidade_texto', '').upper()}\n\n"
             f"\tVem ao exame desta Comissão o presente processo administrativo que trata do pedido de "
             f"{dados.get('modalidade_texto', '').upper()} por parte do(a) Empregado(a) Público(a): {dados.get('nome', '').upper()}.\n\n"
             f"\tConforme o Art. 17 da Lei nº 2.433/2023, a PROMOÇÃO é o desenvolvimento na carreira do empregado público "
             f"municipal que consiste na passagem para a classe imediatamente superior àquela em que se encontra.\n\n")

    if dados['modalidade'] == 'funcional':
        texto += ("\tA PROMOÇÃO FUNCIONAL consiste na passagem do empregado efetivo estável do padrão de vencimento da classe em que se encontra "
                  "para a referência correspondente da classe imediatamente superior, mediante aprovação em avaliações de desempenho e "
                  "realização de cursos de capacitação e ações de desenvolvimento, conforme dispõe o artigo 23 da Lei 2.433/2023.\n\n"
                  "\tNo caso de PROMOÇÃO FUNCIONAL a referida legislação estabelece ainda o interstício de 3 (três) anos de efetivo exercício "
                  "como empregado estável na referência salarial em que se encontra, conforme inciso I do artigo 24 da lei supra.\n\n")
    else:
        texto += ("\tArt. 28. A PROMOÇÃO POR TITULAÇÃO é a passagem do empregado efetivo estável de uma classe para outra imediatamente superior, "
                  "de acordo com os resultados da avaliação de desempenho e a comprovação da formação em curso de nível superior, "
                  "especialização, mestrado ou doutorado, reconhecidos pelo MEC.\n\n")

    texto += "II - ANÁLISE TÉCNICA\n\n1. REQUISITO TEMPORAL (INTERSTÍCIO): "

    if dados['modalidade'] == 'funcional':
        if resultado['tempo_ok']:
            texto += (f"[VERIFICADO] verificou-se que o requerente atingiu o tempo mínimo de 3 (três) anos de efetivo exercício na classe atual, "
                      f"atendendo ao Art. 24, inciso I da Lei 2.433/2023. Tempo decorrido: {resultado['tempo_desc']}.\n\n")
        else:
            texto += (f"[PENDENTE] verificou-se que o requerente NÃO atingiu o interstício mínimo. Atualmente conta com apenas "
                      f"\"{resultado['tempo_desc']}\". Previsão de direito: {resultado['data_futura']}.\n\n")
    else:
        texto += "[ISENTO] Conforme Art. 29 da Lei 2.433/2023, a PROMOÇÃO POR TITULAÇÃO independe de interstício temporal na classe atual.\n\n"

    artigo_eval = "Art. 24, II" if dados['modalidade'] == 'funcional' else "Art. 29, II"
    texto += (f"2. AVALIAÇÃO DE DESEMPENHO: [VERIFICADO] Status: {dados['aval_status']} "
              f"(Nota: {dados['aval_nota']}) ({artigo_eval} da Lei 2.433/2023).\n\n")

    if dados['modalidade'] == 'funcional':
        texto += "3. CAPACITAÇÃO PROFISSIONAL: [VERIFICADO] O(A) Requerente pontuou com os seguintes cursos:\n\n"
        texto += "| CURSO | INSTITUIÇÃO | CARGA | PONTOS |\n|---|---|---|---|\n"
        for c in st.session_state.cursos:
            texto += f"| {c['nome']} | {c['inst']} | {c['horas']}h | {c['pontos']} |\n"
        texto += f"\nTOTAL DE PONTOS: {resultado['total_pontos']} (Mínimo exigido: 40)\n\n"
    else:
        texto += ("3. TITULAÇÃO PROFISSIONAL: [VERIFICADO] O(A) Requerente apresentou formação compatível com o Art. 28:\n\n")
        texto += "| TÍTULO APRESENTADO | INSTITUIÇÃO | CARGA HORÁRIA |\n|---|---|---|\n"
        for c in st.session_state.cursos:
            texto += f"| {c['nome']} | {c['inst']} | {c['horas']}h |\n"
        texto += "\n"

    texto += "III - CONCLUSÃO\n\n"
    if resultado['apto']:
        texto += (f"\tLevando em consideração que o(a) requerente se encontra enquadrado(a) na Classe “{dados['classe_atual']}” "
                  f"desde {dados['data_base'].strftime('%d/%m/%Y')} e que restaram atendidos todos os pressupostos necessários à concessão da {dados['modalidade_texto'].upper()}, "
                  f"esta Comissão opina pelo DEFERIMENTO do pedido, com o enquadramento do(a) servidor(a) na Classe “{dados['classe_nova']}”, “Referência {dados['referencia']}”.\n\n")
    else:
        texto += "\tAnte ao exposto, esta Comissão opina pelo INDEFERIMENTO do pedido pelos seguintes motivos técnicos:\n"
        if resultado['impedimento_art18']: texto += "\t• O servidor incorre em vedações do Art. 18 (Faltas/Suspensão).\n"
        if not resultado['tempo_ok'] and dados['modalidade'] == 'funcional': texto += f"\t• Interstício INSUFICIENTE. Faltam aproximadamente {resultado.get('tempo_restante_meses', 0)} meses.\n"
        if resultado['total_pontos'] < 40 and dados['modalidade'] == 'funcional': texto += f"\t• Pontuação INSUFICIENTE ({resultado['total_pontos']}/40 pts).\n"
        if dados['aval_status'] == 'REPROVADO': texto += "\t• Avaliação de Desempenho insuficiente.\n"

    texto += f"\n\tÉ o parecer.\n\n\tBoa Vista - RR, {date.today().strftime('%d/%m/%Y')}.\n\n\n\t__________________________\n\tPresidente da Comissão"
    
    return texto

# --- INTERFACE PRINCIPAL ---

with st.sidebar:
    st.title("EMHUR CAD")
    st.caption("Sistema de Gestão de Carreira")
    menu = st.radio("Navegação", ["📖 Diretrizes Legais", "⚖️ Análise de Elegibilidade", "📄 Parecer Técnico"])
    st.divider()
    st.info("Ponto de Corte: **40 PONTOS**")

# --- PÁGINA 1: DIRETRIZES LEGAIS ---
if "Diretrizes" in menu:
    st.header("Arquitetura Jurídica (Lei 2.433/2023)")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("**PROMOÇÃO FUNCIONAL (Art. 23)**\n\n40 pontos + 3 anos de interstício.")
    with col2:
        st.info("**PROMOÇÃO POR TITULAÇÃO (Art. 28)**\n\nExige título acadêmico superior.")

# --- PÁGINA 2: ANÁLISE (CALCULADORA) ---
elif "Análise" in menu:
    st.header("Motor de Análise de Elegibilidade")
    
    with st.expander("1. Dados do Requerente e Processo", expanded=True):
        c1, c2, c3 = st.columns(3)
        num_parecer = c1.text_input("Nº Parecer", "001/2026")
        nup = c2.text_input("NUP", "9.000000/2026")
        modalidade = c3.selectbox("Modalidade", ["Funcional (Art. 23)", "Titulação (Art. 28)"])
        modalidade_key = 'funcional' if 'Funcional' in modalidade else 'titulacao'

        c4, c5, c6 = st.columns(3)
        nome = c4.text_input("Nome do Servidor")
        data_base = c5.date_input("Data da Última Promoção", date(2023, 1, 1))
        aval_status = c6.selectbox("Avaliação Desempenho", ["APROVADO", "REPROVADO", "NÃO HOUVE"])
        aval_nota = c6.number_input("Nota Avaliação", 0, 100, 0)

        c7, c8 = st.columns(2)
        classe_atual = c7.text_input("Classe Atual", "A")
        referencia = c8.text_input("Referência Atual", "7")

    with st.expander("2. Impedimentos Legais (Art. 18)", expanded=True):
        imp1 = st.checkbox("I – Punido com pena de suspensão no período")
        imp2 = st.checkbox("II – Mais de 20 faltas injustificadas")
        imp3 = st.checkbox("III – Contrato de trabalho suspenso")
        impedimento_ativo = imp1 or imp2 or imp3

    with st.expander("3. Cursos e Títulos", expanded=True):
        cc1, cc2 = st.columns([3, 1])
        with cc1:
            novo_curso = st.text_input("Nome do Curso/Título")
            inst_curso = st.text_input("Instituição")
        with cc2:
            horas_curso = st.number_input("Carga Horária", min_value=0, step=1)
            relacao_curso = st.selectbox("Relação", ["DIRETA", "CORRELATA"])
        
        if st.button("➕ Adicionar Curso"):
            if novo_curso and horas_curso > 0:
                pts = calcular_pontos(horas_curso, relacao_curso) if modalidade_key == 'funcional' else 0
                st.session_state.cursos.append({
                    "nome": novo_curso, "inst": inst_curso, 
                    "horas": horas_curso, "relacao": relacao_curso, 
                    "pontos": pts
                })
                st.success("Curso adicionado!")
                force_rerun()

        # Lista de Cursos
        if st.session_state.cursos:
            st.markdown("---")
            for i, c in enumerate(st.session_state.cursos):
                cols = st.columns([4, 2, 1, 1])
                cols[0].text(f"{i+1}. {c['nome']}")
                cols[1].text(f"{c['relacao']}")
                cols[2].text(f"{c['horas']}h")
                if cols[3].button("🗑️", key=f"del_{i}"):
                    st.session_state.cursos.pop(i)
                    force_rerun()

    if st.button("CALCULAR ELEGIBILIDADE", type="primary"):
        hoje = date.today()
        
        # Cálculo de tempo (3 anos = 1095 dias aprox, mas usamos lógica de ano)
        anos, meses, dias = calcular_intersticio(data_base, hoje)
        tempo_desc = f"{anos} anos, {meses} meses e {dias} dias"
        tempo_ok = anos >= 3
        
        # Previsão data futura simples
        try:
            data_futura = data_base.replace(year=data_base.year + 3)
        except ValueError: # Tratamento bissexto
            data_futura = date(data_base.year + 3, 3, 1)
            
        data_futura_str = data_futura.strftime('%d/%m/%Y')
        
        # Pontos
        total_pontos = sum(c['pontos'] for c in st.session_state.cursos)

        # Regra Final
        is_apto = False
        if not impedimento_ativo:
            if modalidade_key == 'funcional':
                if tempo_ok and total_pontos >= 40 and aval_status != 'REPROVADO':
                    is_apto = True
            else: # Titulação
                if aval_status != 'REPROVADO' and len(st.session_state.cursos) > 0:
                    is_apto = True

        st.session_state.dados_parecer = {
            'num': num_parecer, 'nup': nup, 'nome': nome, 
            'modalidade': modalidade_key, 'modalidade_texto': "Promoção Funcional" if modalidade_key == 'funcional' else "Promoção por Titulação",
            'data_base': data_base, 'aval_status': aval_status, 'aval_nota': aval_nota,
            'classe_atual': classe_atual, 'classe_nova': proxima_classe(classe_atual), 'referencia': referencia
        }
        
        st.session_state.resultado_analise = {
            'tempo_ok': tempo_ok, 'tempo_desc': tempo_desc,
            'data_futura': data_futura_str,
            'tempo_restante_meses': (36 - (anos * 12 + meses)) if not tempo_ok else 0,
            'total_pontos': total_pontos, 'impedimento_art18': impedimento_ativo,
            'apto': is_apto
        }
        
        st.session_state.analise_realizada = True
        force_rerun()

    # Dashboard Resultados
    if st.session_state.analise_realizada:
        res = st.session_state.resultado_analise
        # Recupera modalidade salva para não dar erro se mudar o selectbox depois
        mod_salva = st.session_state.dados_parecer.get('modalidade', 'funcional')
        
        st.markdown("---")
        st.subheader("Resultado da Análise Técnica")
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.metric("Tempo Decorrido", f"{res['tempo_desc'].split(',')[0]}", delta="Ok" if res['tempo_ok'] else "Insuficiente")
        dc2.metric("Pontuação", f"{res['total_pontos']} pts", delta=f"{res['total_pontos']-40}" if mod_salva == 'funcional' else None)
        dc3.metric("Impedimentos Art. 18", "Sim" if res['impedimento_art18'] else "Não", delta="Ok" if not res['impedimento_art18'] else "Bloqueio", delta_color="inverse")
        dc4.metric("Parecer Final", "DEFERIMENTO" if res['apto'] else "INDEFERIMENTO", delta_color="normal" if res['apto'] else "inverse")

# --- PÁGINA 3: RELATÓRIO ---
elif "Parecer" in menu:
    if not st.session_state.analise_realizada:
        st.warning("Por favor, realize a Análise de Elegibilidade primeiro na aba lateral.")
    else:
        st.header("Minuta Administrativa Final")
        texto_final = gerar_parecer(st.session_state.dados_parecer, st.session_state.resultado_analise)
        st.code(texto_final, language=None)
        st.caption("Copie o texto acima.")
        
        st.code(texto_final, language=None)
        st.caption("Copie o texto acima clicando no ícone de cópia no canto superior direito do bloco.")

    )
