import sqlite3
import os

DB_PATH = 'comissoes_v5.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de Vendedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        taxa_padrao TEXT DEFAULT '0.50',
        ativo BOOLEAN DEFAULT 1
    )
    ''')
    
    # Tabela de Vendas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_venda_origem TEXT NOT NULL,
        id_vendedor INTEGER NOT NULL,
        data_venda TEXT,
        cliente TEXT,
        valor_bruto TEXT NOT NULL,
        percentual_comissao TEXT NOT NULL,
        valor_comissao TEXT NOT NULL,
        status_fechamento TEXT DEFAULT 'PENDENTE',
        forma_pagamento TEXT,
        data_pagamento TEXT,
        data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(id_vendedor) REFERENCES vendedores(id),
        UNIQUE(id_venda_origem, id_vendedor)
    )
    ''')
    
    # Tabela de Fechamentos / Auditoria
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_fechamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_vendedor INTEGER,
        periodo_referencia TEXT,
        total_vendas INTEGER,
        total_bruto TEXT,
        total_comissao TEXT,
        data_fechamento DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(id_vendedor) REFERENCES vendedores(id)
    )
    ''')
    
    conn.commit()
    conn.close()
