import streamlit as st
import os
import io
import pandas as pd
from datetime import datetime
from app.database import db
from app.ui.styles import apply_custom_css
from app.use_cases.import_pipeline import ImportPipeline

st.set_page_config(
    page_title="Uniodonto Resende - ERP Comissões",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_custom_css()
db.init_db()

LOGO_DIR = "assets"
LOGO_FILE = os.path.join(LOGO_DIR, "logo.png")

def format_currency(val):
    try:
        val_f = float(val)
        return f"R$ {val_f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def render_sidebar():
    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, use_container_width=True)
        else:
            st.markdown("### Logo Institucional")
            up = st.file_uploader("Carregar Logo Uniodonto (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
            if up:
                os.makedirs(LOGO_DIR, exist_ok=True)
                with open(LOGO_FILE, "wb") as f:
                    f.write(up.getbuffer())
                st.rerun()
        
        st.markdown("---")
        st.markdown("**SISTEMA DE GESTÃO ERP**")
        return st.radio(
            "Módulos:",
            [
                "📊 1. Painel Geral",
                "📥 2. Importação de Vendas",
                "🔍 3. Memória de Cálculo & Extratos",
                "💰 4. Fechamento & Pagamentos",
                "📄 5. Exportação Financeira"
            ],
            label_visibility="collapsed"
        )

menu = render_sidebar()

# ==============================================================================
# 1. PAINEL GERAL (DASHBOARD)
# ==============================================================================
if menu == "📊 1. Painel Geral":
    st.title("Painel Geral de Vendas & Comissões")
    
    conn = db.get_connection()
    df = pd.read_sql('''
        SELECT v.id_venda_origem, vd.nome as Vendedor, v.valor_bruto, v.valor_comissao, v.status_fechamento, v.data_venda, v.cliente 
        FROM vendas v JOIN vendedores vd ON v.id_vendedor = vd.id
    ''', conn)
    conn.close()
    
    if df.empty:
        st.info("Nenhuma venda cadastrada no sistema. Vá ao módulo '📥 2. Importação de Vendas' para importar seu relatório.")
    else:
        df['valor_bruto'] = df['valor_bruto'].astype(float)
        df['valor_comissao'] = df['valor_comissao'].astype(float)
        
        total_bruto = df['valor_bruto'].sum()
        total_pendente = df[df['status_fechamento'] == 'PENDENTE']['valor_comissao'].sum()
        total_pago = df[df['status_fechamento'] == 'PAGO']['valor_comissao'].sum()
        total_comissao = df['valor_comissao'].sum()
        qtd_vendas = len(df)
        vendedores_ativos = df['Vendedor'].nunique()
        
        # Cards de Indicadores
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faturamento Total de Vendas", format_currency(total_bruto), f"{qtd_vendas} vendas registradas")
        c2.metric("Comissões Totais Calculadas", format_currency(total_comissao), f"{vendedores_ativos} vendedores")
        c3.metric("Comissões Pendentes (A Pagar)", format_currency(total_pendente))
        c4.metric("Comissões Já Pagas", format_currency(total_pago))
        
        st.markdown("---")
        
        # Tabs de Análise
        tab1, tab2 = st.tabs(["🏆 Resumo e Ranking por Vendedor", "📊 Comparativo Visual"])
        
        with tab1:
            st.subheader("Quadro de Comissões por Vendedor")
            
            resumo = df.groupby('Vendedor').agg(
                Qtd_Vendas=('id_venda_origem', 'count'),
                Total_Vendido=('valor_bruto', 'sum'),
                Comissao_Calculada=('valor_comissao', 'sum')
            ).reset_index()
            
            # Adicionar pendente e pago por vendedor
            pendentes_v = df[df['status_fechamento'] == 'PENDENTE'].groupby('Vendedor')['valor_comissao'].sum()
            pagos_v = df[df['status_fechamento'] == 'PAGO'].groupby('Vendedor')['valor_comissao'].sum()
            
            resumo['A_Pagar'] = resumo['Vendedor'].map(pendentes_v).fillna(0.0)
            resumo['Pago'] = resumo['Vendedor'].map(pagos_v).fillna(0.0)
            
            # Formatação para visualização
            resumo_disp = resumo.copy()
            resumo_disp['Total_Vendido'] = resumo_disp['Total_Vendido'].apply(format_currency)
            resumo_disp['Taxa_Comissao'] = "50%"
            resumo_disp['Comissao_Calculada'] = resumo_disp['Comissao_Calculada'].apply(format_currency)
            resumo_disp['A_Pagar'] = resumo_disp['A_Pagar'].apply(format_currency)
            resumo_disp['Pago'] = resumo_disp['Pago'].apply(format_currency)
            
            resumo_disp.columns = [
                'Vendedor', 'Qtd Vendas', 'Total Vendido (R$)', 'Comissão Total (R$)',
                'Saldo a Pagar (R$)', 'Total Pago (R$)', 'Taxa Aplicada'
            ]
            st.dataframe(resumo_disp, use_container_width=True, hide_index=True)
            
        with tab2:
            st.subheader("Volume de Vendas e Comissões")
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.markdown("**Total Vendido por Vendedor (R$)**")
                vendas_chart = df.groupby('Vendedor')['valor_bruto'].sum().reset_index()
                st.bar_chart(vendas_chart.set_index('Vendedor'), color="#7b1fa2")
            with col_chart2:
                st.markdown("**Comissão Calculada por Vendedor (R$)**")
                comissao_chart = df.groupby('Vendedor')['valor_comissao'].sum().reset_index()
                st.bar_chart(comissao_chart.set_index('Vendedor'), color="#9c27b0")

# ==============================================================================
# 2. IMPORTAÇÃO DE VENDAS
# ==============================================================================
elif menu == "📥 2. Importação de Vendas":
    st.title("Importação Transacional de Relatórios")
    st.markdown("Envie o relatório de vendas em formato **Excel (.xlsx, .xls)** ou **CSV**.")
    
    arquivo = st.file_uploader("Selecione o arquivo de vendas:", type=['xlsx', 'xls', 'csv'])
    
    if arquivo:
        try:
            if arquivo.name.endswith(('.xlsx', '.xls')):
                df_raw = pd.read_excel(arquivo)
            else:
                df_raw = pd.read_csv(arquivo, sep=None, engine='python')
                
            st.subheader("1. Pré-visualização do Arquivo")
            st.dataframe(df_raw.head(4), use_container_width=True)
            
            st.subheader("2. Mapeamento Automático de Colunas")
            cols = list(df_raw.columns)
            cols_opcionais = ["(Não Mapear)"] + cols
            
            def match_col(options, keywords):
                for i, opt in enumerate(options):
                    if opt == "(Não Mapear)": continue
                    if any(k.lower() in opt.lower() for k in keywords):
                        return i
                return 0

            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                m_vend = c1.selectbox("👤 Nome do Vendedor *", cols, index=match_col(cols, ['vendedor', 'nome', 'consultor']))
                m_id = c2.selectbox("🏷️ Código / ID da Venda *", cols, index=match_col(cols, ['cód', 'cod', 'id', 'venda', 'pedido']))
                m_val = c3.selectbox("💰 Valor Bruto da Venda *", cols, index=match_col(cols, ['valor', 'bruto', 'total', 'preço', 'preco']))
                
                c4, c5, c6 = st.columns(3)
                m_data = c4.selectbox("📅 Data da Venda (Opcional)", cols_opcionais, index=match_col(cols_opcionais, ['data', 'emissao', 'emissão']))
                m_cli = c5.selectbox("🤝 Cliente / Paciente (Opcional)", cols_opcionais, index=match_col(cols_opcionais, ['cliente', 'paciente', 'empresa']))
                taxa_percentual = c6.number_input("⚙️ Taxa de Comissão Padrão (%)", value=50.0, step=1.0)
            
            if st.button("🚀 Processar e Gravar no ERP", type="primary", use_container_width=True):
                m_data_real = None if m_data == "(Não Mapear)" else m_data
                m_cli_real = None if m_cli == "(Não Mapear)" else m_cli
                taxa_decimal = taxa_percentual / 100.0
                
                pipeline = ImportPipeline(df_raw, m_vend, m_id, m_val, m_data_real, m_cli_real, taxa_decimal)
                with st.spinner("Validando transação com precisão financeira e travas de integridade..."):
                    qtd_sucesso, erros = pipeline.executar()
                
                if erros:
                    st.warning("⚠️ Ocorrências identificadas durante a importação:")
                    for err in erros:
                        st.write(f"• {err}")
                if qtd_sucesso > 0:
                    st.success(f"✅ {qtd_sucesso} vendas inseridas com sucesso e comissões calculadas a {taxa_percentual}%!")
                    
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")

# ==============================================================================
# 3. MEMÓRIA DE CÁLCULO & EXTRATOS DETALHADOS
# ==============================================================================
elif menu == "🔍 3. Memória de Cálculo & Extratos":
    st.title("Memória de Cálculo & Extrato por Vendedor")
    st.markdown("Confira exatamente como cada comissão foi apurada, venda por venda, com transparência total.")
    
    conn = db.get_connection()
    df_vendas = pd.read_sql('''
        SELECT v.id_venda_origem as Venda, vd.nome as Vendedor, v.data_venda as Data, v.cliente as Cliente,
               v.valor_bruto as Bruto, v.percentual_comissao as Taxa, v.valor_comissao as Comissao, v.status_fechamento as Status
        FROM vendas v JOIN vendedores vd ON v.id_vendedor = vd.id
    ''', conn)
    conn.close()
    
    if df_vendas.empty:
        st.info("Nenhuma venda disponível para apuração.")
    else:
        df_vendas['Bruto'] = df_vendas['Bruto'].astype(float)
        df_vendas['Comissao'] = df_vendas['Comissao'].astype(float)
        
        lista_vendedores = sorted(df_vendas['Vendedor'].unique().tolist())
        vendedor_sel = st.selectbox("Selecione o Vendedor para conferência:", lista_vendedores)
        
        df_vend = df_vendas[df_vendas['Vendedor'] == vendedor_sel].copy()
        
        tot_vendido = df_vend['Bruto'].sum()
        tot_comissao = df_vend['Comissao'].sum()
        tot_pendente = df_vend[df_vend['Status'] == 'PENDENTE']['Comissao'].sum()
        tot_pago = df_vend[df_vend['Status'] == 'PAGO']['Comissao'].sum()
        
        # Cards do Vendedor
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Vendido", format_currency(tot_vendido), f"{len(df_vend)} vendas")
        c2.metric("Comissão Apurada (50%)", format_currency(tot_comissao))
        c3.metric("Saldo Pendente", format_currency(tot_pendente))
        c4.metric("Valor Já Pago", format_currency(tot_pago))
        
        st.markdown(f"### Detalhamento das Vendas — {vendedor_sel}")
        st.caption("Fórmula aplicada: Comissão = Valor Bruto da Venda × Taxa (50%)")
        
        df_disp = df_vend.copy()
        df_disp['Bruto'] = df_disp['Bruto'].apply(format_currency)
        df_disp['Comissao'] = df_disp['Comissao'].apply(format_currency)
        df_disp['Taxa'] = df_disp['Taxa'].apply(lambda x: f"{float(x)*100:.0f}%")
        
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
        
        # Exportação Individual
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_vend.to_excel(writer, index=False, sheet_name=f'Extrato_{vendedor_sel[:10]}')
        st.download_button(
            label=f"📥 Baixar Extrato de {vendedor_sel} em Excel",
            data=buffer.getvalue(),
            file_name=f"extrato_comissoes_{vendedor_sel.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==============================================================================
# 4. FECHAMENTO & PAGAMENTOS
# ==============================================================================
elif menu == "💰 4. Fechamento & Pagamentos":
    st.title("Centro de Fechamento & Pagamento de Comissões")
    
    conn = db.get_connection()
    df_pendentes = pd.read_sql('''
        SELECT v.id as ID, vd.nome as Vendedor, v.id_venda_origem as Venda, v.data_venda as Data,
               v.cliente as Cliente, v.valor_bruto as Bruto, v.valor_comissao as Comissao, v.status_fechamento as Status
        FROM vendas v JOIN vendedores vd ON v.id_vendedor = vd.id
        WHERE v.status_fechamento = 'PENDENTE'
    ''', conn)
    
    df_pagas = pd.read_sql('''
        SELECT v.id as ID, vd.nome as Vendedor, v.id_venda_origem as Venda, v.data_venda as Data,
               v.cliente as Cliente, v.valor_bruto as Bruto, v.valor_comissao as Comissao,
               v.forma_pagamento as Forma, v.data_pagamento as Data_Pagamento
        FROM vendas v JOIN vendedores vd ON v.id_vendedor = vd.id
        WHERE v.status_fechamento = 'PAGO'
    ''', conn)
    conn.close()
    
    tab_pend, tab_hist = st.tabs(["🔴 Comissões Pendentes para Pagamento", "🟢 Histórico de Pagamentos Confirmados"])
    
    with tab_pend:
        if df_pendentes.empty:
            st.success("🎉 Todas as comissões apuradas já foram pagas! Não há valores pendentes.")
        else:
            df_pendentes['Bruto'] = df_pendentes['Bruto'].astype(float)
            df_pendentes['Comissao'] = df_pendentes['Comissao'].astype(float)
            
            total_pend_valor = df_pendentes['Comissao'].sum()
            st.markdown(f"### Total Geral Pendente: **{format_currency(total_pend_valor)}**")
            
            # Opção de pagar por vendedor ou todos
            vends_pend = ["Todos os Vendedores"] + sorted(df_pendentes['Vendedor'].unique().tolist())
            col_sel, col_forma, col_data = st.columns(3)
            vend_escolhido = col_sel.selectbox("Pagar para:", vends_pend)
            forma_pag = col_forma.selectbox("Forma de Pagamento:", ["Transferência / PIX", "Boleto", "Cheque", "Dinheiro", "Crédito em Folha"])
            data_pag = col_data.date_input("Data do Pagamento:", datetime.now())
            
            # Filtrar tabela se selecionou um vendedor específico
            df_acao = df_pendentes if vend_escolhido == "Todos os Vendedores" else df_pendentes[df_pendentes['Vendedor'] == vend_escolhido]
            
            valor_a_pagar = df_acao['Comissao'].sum()
            st.info(f"Valor a ser liquidado para {vend_escolhido}: **{format_currency(valor_a_pagar)}** ({len(df_acao)} vendas)")
            
            df_acao_disp = df_acao.copy()
            df_acao_disp['Bruto'] = df_acao_disp['Bruto'].apply(format_currency)
            df_acao_disp['Comissao'] = df_acao_disp['Comissao'].apply(format_currency)
            st.dataframe(df_acao_disp[['Vendedor', 'Venda', 'Data', 'Cliente', 'Bruto', 'Comissao']], use_container_width=True, hide_index=True)
            
            if st.button(f"✅ Confirmar e Baixar Pagamento ({vend_escolhido})", type="primary"):
                conn = db.get_connection()
                c = conn.cursor()
                data_str = data_pag.strftime("%d/%m/%Y")
                if vend_escolhido == "Todos os Vendedores":
                    c.execute('''UPDATE vendas SET status_fechamento = 'PAGO', forma_pagamento = ?, data_pagamento = ?
                                 WHERE status_fechamento = 'PENDENTE' ''', (forma_pag, data_str))
                else:
                    c.execute('''UPDATE vendas SET status_fechamento = 'PAGO', forma_pagamento = ?, data_pagamento = ?
                                 WHERE status_fechamento = 'PENDENTE' AND id_vendedor = (SELECT id FROM vendedores WHERE nome = ?)''',
                              (forma_pag, data_str, vend_escolhido))
                conn.commit()
                conn.close()
                st.success(f"Pagamento de {format_currency(valor_a_pagar)} registrado com sucesso!")
                st.rerun()
                
    with tab_hist:
        if df_pagas.empty:
            st.info("Nenhum pagamento registrado no histórico.")
        else:
            df_pagas['Bruto'] = df_pagas['Bruto'].astype(float)
            df_pagas['Comissao'] = df_pagas['Comissao'].astype(float)
            
            total_pago_hist = df_pagas['Comissao'].sum()
            st.markdown(f"### Total Histórico Pago: **{format_currency(total_pago_hist)}**")
            
            df_pagas_disp = df_pagas.copy()
            df_pagas_disp['Bruto'] = df_pagas_disp['Bruto'].apply(format_currency)
            df_pagas_disp['Comissao'] = df_pagas_disp['Comissao'].apply(format_currency)
            st.dataframe(df_pagas_disp[['Vendedor', 'Venda', 'Data', 'Cliente', 'Bruto', 'Comissao', 'Forma', 'Data_Pagamento']], use_container_width=True, hide_index=True)

# ==============================================================================
# 5. EXPORTAÇÃO FINANCEIRA
# ==============================================================================
elif menu == "📄 5. Exportação Financeira":
    st.title("Exportação de Relatórios Financeiros")
    st.markdown("Exporte os dados completos do ERP para auditoria, contabilidade ou envio aos vendedores.")
    
    conn = db.get_connection()
    df_todos = pd.read_sql('''
        SELECT v.id_venda_origem as Cod_Venda, vd.nome as Vendedor, v.data_venda as Data_Venda,
               v.cliente as Cliente, v.valor_bruto as Valor_Bruto, v.percentual_comissao as Taxa,
               v.valor_comissao as Valor_Comissao, v.status_fechamento as Status_Pagamento,
               v.forma_pagamento as Forma_Pagamento, v.data_pagamento as Data_Pagamento
        FROM vendas v JOIN vendedores vd ON v.id_vendedor = vd.id
    ''', conn)
    conn.close()
    
    if df_todos.empty:
        st.info("Nenhum dado cadastrado para exportação.")
    else:
        df_todos['Valor_Bruto'] = df_todos['Valor_Bruto'].astype(float)
        df_todos['Valor_Comissao'] = df_todos['Valor_Comissao'].astype(float)
        
        # Resumo consolidado por vendedor
        resumo_geral = df_todos.groupby('Vendedor').agg(
            Qtd_Vendas=('Cod_Venda', 'count'),
            Total_Vendido=('Valor_Bruto', 'sum'),
            Total_Comissao=('Valor_Comissao', 'sum')
        ).reset_index()
        
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.subheader("1. Folha de Comissões Completa (Excel)")
            st.write("Planilha com duas abas: Resumo por Vendedor e Todas as Vendas Detalhadas.")
            
            buf_excel = io.BytesIO()
            with pd.ExcelWriter(buf_excel, engine='openpyxl') as writer:
                resumo_geral.to_excel(writer, index=False, sheet_name='Resumo_Vendedores')
                df_todos.to_excel(writer, index=False, sheet_name='Todas_Vendas')
                
            st.download_button(
                label="📥 Baixar Folha Consolidada (.xlsx)",
                data=buf_excel.getvalue(),
                file_name=f"uniodonto_folha_comissoes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        with col_exp2:
            st.subheader("2. Arquivo CSV para Integração Contábil")
            st.write("Exportação compatível com sistemas financeiros e ERPs externos.")
            
            csv_data = df_todos.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar Relatório Completo (.csv)",
                data=csv_data,
                file_name=f"uniodonto_relatorio_vendas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
