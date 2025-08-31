#!/usr/bin/env python3
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')  # evita problemas de cache em containers
import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # backend para ambiente sem display
import matplotlib.pyplot as plt

# ---------------------------
# Conexão
# ---------------------------
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'db'),
            user=os.getenv('DB_USER', 'enova_user'),
            password=os.getenv('DB_PASS', 'enova_pass'),
            database=os.getenv('DB_NAME', 'enova'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return conn
    except mysql.connector.Error as e:
        print("Erro ao conectar ao MySQL:", e)
        return None

# ---------------------------
# Criar tabela (fallback)
# ---------------------------
def criar_tabela():
    conn = get_connection()
    if not conn:
        print("Sem conexão para criar tabela.")
        return
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS t_enova_analise_eficiencia (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dt_analise DATE NOT NULL,
            nr_producao_energia DECIMAL(10,2) NOT NULL,
            nr_consumo_energia DECIMAL(10,2) NOT NULL,
            nr_eficiencia DECIMAL(10,2) NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tabela verificada/criada.")

# ---------------------------
# Gerar datas e dados simulados
# ---------------------------
def gerar_datas(inicio, fim, n):
    dias = (fim - inicio).days
    return [inicio + timedelta(days=int(np.random.randint(0, max(1,dias)))) for _ in range(n)]

def gerar_dados_simulados(n, inicio=None, fim=None):
    if inicio is None: inicio = datetime(2023,1,1)
    if fim is None: fim = datetime(2024,1,1)
    datas = gerar_datas(inicio, fim, n)
    nr_producao = np.round(np.random.uniform(1000, 5000, n), 2)
    nr_consumo = np.round(np.random.uniform(800, 4500, n), 2)
    nr_eficiencia = np.round((nr_producao / nr_consumo) * 100, 2)
    df = pd.DataFrame({
        'dt_analise': [d.date() for d in datas],
        'nr_producao_energia': nr_producao,
        'nr_consumo_energia': nr_consumo,
        'nr_eficiencia': nr_eficiencia
    })
    return df

# ---------------------------
# Inserção em lote a partir de DataFrame
# ---------------------------
def inserir_dados_df(df, tabela='t_enova_analise_eficiencia'):
    conn = get_connection()
    if not conn:
        print("Sem conexão para inserir dados.")
        return
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(f"""
            INSERT INTO {tabela} (dt_analise, nr_producao_energia, nr_consumo_energia, nr_eficiencia)
            VALUES (%s, %s, %s, %s)
        """, (row['dt_analise'].strftime('%Y-%m-%d') if hasattr(row['dt_analise'], 'strftime') else str(row['dt_analise']),
              float(row['nr_producao_energia']),
              float(row['nr_consumo_energia']),
              float(row['nr_eficiencia'])))
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(df)} registros inseridos na tabela {tabela}.")

# ---------------------------
# Consultas (retornam DataFrame)
# ---------------------------
def consultar_todos():
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    cur = conn.cursor()
    cur.execute("SELECT id, dt_analise, nr_producao_energia, nr_consumo_energia, nr_eficiencia FROM t_enova_analise_eficiencia ORDER BY dt_analise")
    rows = cur.fetchall()
    cols = ['id', 'dt_analise', 'nr_producao_energia', 'nr_consumo_energia', 'nr_eficiencia']
    df = pd.DataFrame(rows, columns=cols)
    cur.close()
    conn.close()
    return df

def consultar_por_id(id_analise):
    conn = get_connection()
    if not conn: return None
    cur = conn.cursor()
    cur.execute("SELECT id, dt_analise, nr_producao_energia, nr_consumo_energia, nr_eficiencia FROM t_enova_analise_eficiencia WHERE id = %s", (id_analise,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def consultar_eficiencia_abaixo(limite):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    cur = conn.cursor()
    cur.execute("SELECT id, dt_analise, nr_producao_energia, nr_consumo_energia, nr_eficiencia FROM t_enova_analise_eficiencia WHERE nr_eficiencia < %s ORDER BY nr_eficiencia ASC", (limite,))
    rows = cur.fetchall()
    cols = ['id', 'dt_analise', 'nr_producao_energia', 'nr_consumo_energia', 'nr_eficiencia']
    df = pd.DataFrame(rows, columns=cols)
    cur.close()
    conn.close()
    return df

def consultar_por_intervalo(data_inicio, data_fim):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    cur = conn.cursor()
    cur.execute("SELECT id, dt_analise, nr_producao_energia, nr_consumo_energia, nr_eficiencia FROM t_enova_analise_eficiencia WHERE dt_analise BETWEEN %s AND %s ORDER BY dt_analise", (data_inicio, data_fim))
    rows = cur.fetchall()
    cols = ['id', 'dt_analise', 'nr_producao_energia', 'nr_consumo_energia', 'nr_eficiencia']
    df = pd.DataFrame(rows, columns=cols)
    cur.close()
    conn.close()
    return df

# ---------------------------
# Update / Delete / Insert manual
# ---------------------------
def atualizar_analise(id_analise, producao, consumo, eficiencia):
    conn = get_connection()
    if not conn: return
    cur = conn.cursor()
    cur.execute("""
        UPDATE t_enova_analise_eficiencia
        SET nr_producao_energia=%s, nr_consumo_energia=%s, nr_eficiencia=%s
        WHERE id=%s
    """, (producao, consumo, eficiencia, id_analise))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Registro {id_analise} atualizado.")

def deletar_analise(id_analise):
    conn = get_connection()
    if not conn: return
    cur = conn.cursor()
    cur.execute("DELETE FROM t_enova_analise_eficiencia WHERE id=%s", (id_analise,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Registro {id_analise} deletado.")

def inserir_analise_manual(data_str, producao, consumo, eficiencia):
    conn = get_connection()
    if not conn: return
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO t_enova_analise_eficiencia (dt_analise, nr_producao_energia, nr_consumo_energia, nr_eficiencia)
        VALUES (%s, %s, %s, %s)
    """, (data_str, producao, consumo, eficiencia))
    conn.commit()
    cur.close()
    conn.close()
    print("Inserção manual realizada.")

# ---------------------------
# Export JSON e gráfico (salva em /app)
# ---------------------------
def exportar_json(caminho='dados_exportados.json'):
    df = consultar_todos()
    if df.empty:
        print("Nenhum dado para exportar.")
        return
    df.to_json(caminho, orient='records', date_format='iso')
    print(f"Exportado para {caminho}")

def gerar_grafico(caminho='grafico_eficiencia.png'):
    df = consultar_todos()
    if df.empty:
        print("Nenhum dado para gerar gráfico.")
        return
    df['dt_analise'] = pd.to_datetime(df['dt_analise'])
    plt.figure(figsize=(10,5))
    plt.plot(df['dt_analise'], df['nr_eficiencia'], marker='o')
    plt.title('Evolução da Eficiência')
    plt.xlabel('Data')
    plt.ylabel('Eficiência (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()
    print(f"Gráfico salvo em {caminho}")

# ---------------------------
# Menu CLI
# ---------------------------
def menu():
    criar_tabela()  # garante existência caso init.sql não tenha rodado
    while True:
        print("\n==== MENU ====")
        print("1  - Gerar dados simulados (apenas em memória)")
        print("2  - Inserir dados (do último gerado) no banco")
        print("3  - Consultar todos os dados")
        print("4  - Gerar gráfico (salva PNG)")
        print("5  - Exportar JSON")
        print("6  - Consultar por ID")
        print("7  - Consultar eficiência abaixo de valor")
        print("8  - Consultar por intervalo de datas")
        print("9  - Atualizar análise por ID")
        print("10 - Deletar análise por ID")
        print("11 - Inserir análise manualmente")
        print("0  - Sair")
        escolha = input("Escolha: ").strip()
        try:
            if escolha == '1':
                n = int(input("Quantos registros gerar? "))
                globals()['_df_tmp'] = gerar_dados_simulados(n)
                print(f"{n} registros gerados (em memória). Use opção 2 para inserir no DB.")
            elif escolha == '2':
                if '_df_tmp' not in globals():
                    print("Nenhum dado gerado. Use opção 1 primeiro.")
                else:
                    inserir_dados_df(globals()['_df_tmp'])
            elif escolha == '3':
                df = consultar_todos()
                if df.empty:
                    print("Nenhum registro encontrado.")
                else:
                    print(df.to_string(index=False))
            elif escolha == '4':
                gerar_grafico()
            elif escolha == '5':
                exportar_json()
            elif escolha == '6':
                idv = int(input("ID: "))
                row = consultar_por_id(idv)
                print(row if row else "Não encontrado")
            elif escolha == '7':
                lim = float(input("Limite de eficiência (%): "))
                df = consultar_eficiencia_abaixo(lim)
                print(df.to_string(index=False) if not df.empty else "Nenhum registro")
            elif escolha == '8':
                di = input("Data início (YYYY-MM-DD): ")
                df = consultar_por_intervalo(di, input("Data fim (YYYY-MM-DD): "))
                print(df.to_string(index=False) if not df.empty else "Nenhum registro")
            elif escolha == '9':
                idv = int(input("ID: "))
                p = float(input("Produção: "))
                c = float(input("Consumo: "))
                e = float(input("Eficiência: "))
                atualizar_analise(idv, p, c, e)
            elif escolha == '10':
                idv = int(input("ID para deletar: "))
                deletar_analise(idv)
            elif escolha == '11':
                d = input("Data (YYYY-MM-DD): ")
                p = float(input("Produção: "))
                c = float(input("Consumo: "))
                e = float(input("Eficiência: "))
                inserir_analise_manual(d, p, c, e)
            elif escolha == '0':
                print("Saindo...")
                break
            else:
                print("Opção inválida.")
        except Exception as ex:
            print("Erro:", ex)

if __name__ == "__main__":
    menu()
