import pandas as pd
from decimal import Decimal
from app.database import db
from app.domain.calculo import calcular_comissao
import sqlite3

class ImportPipeline:
    def __init__(self, df, map_vend, map_id, map_val, map_data, map_cli, taxa):
        self.df = df
        self.map_vend = map_vend
        self.map_id = map_id
        self.map_val = map_val
        self.map_data = map_data
        self.map_cli = map_cli
        self.taxa = str(taxa)
        
    def executar(self):
        regs, erros = [], []
        for i, (idx, row) in enumerate(self.df.iterrows()):
            try:
                v = str(row[self.map_vend]).strip()
                id_v = str(row[self.map_id]).strip()
                
                # Tratamento financeiro monetário rigoroso
                val_raw = str(row[self.map_val]).upper().replace('R$', '').replace(' ', '').strip()
                if ',' in val_raw and '.' in val_raw:
                    val_raw = val_raw.replace('.', '')
                val_raw = val_raw.replace(',', '.')
                val_dec = Decimal(val_raw)
                
                com = calcular_comissao(val_dec, self.taxa)
                dt = str(row[self.map_data]).strip() if self.map_data and pd.notna(row[self.map_data]) else "-"
                cli = str(row[self.map_cli]).strip() if self.map_cli and pd.notna(row[self.map_cli]) else "-"
                
                regs.append((v, id_v, str(val_dec), str(com), dt, cli))
            except Exception as e:
                erros.append(f"Linha {i+2}: Formatação inválida ou valor ausente.")
                
        inseridos = 0
        if regs:
            conn = db.get_connection()
            try:
                c = conn.cursor()
                c.execute("BEGIN TRANSACTION")
                for r in regs:
                    c.execute("INSERT OR IGNORE INTO vendedores (nome, taxa_padrao) VALUES (?, ?)", (r[0], self.taxa))
                    c.execute("SELECT id FROM vendedores WHERE nome = ?", (r[0],))
                    v_id = c.fetchone()[0]
                    try:
                        c.execute('''INSERT INTO vendas (id_venda_origem, id_vendedor, valor_bruto, percentual_comissao, valor_comissao, data_venda, cliente)
                                     VALUES (?,?,?,?,?,?,?)''', (r[1], v_id, r[2], self.taxa, r[3], r[4], r[5]))
                        inseridos += 1
                    except sqlite3.IntegrityError:
                        erros.append(f"Venda '{r[1]}' do vendedor '{r[0]}' ignorada: código já cadastrado no sistema (duplicidade prevenida).")
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        return inseridos, erros
