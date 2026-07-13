
"""
GastouQuanto - Controle Financeiro Pessoal
Equivalente Python do app Android original.

Dependências:
    pip install matplotlib

Uso:
    python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import os
from datetime import datetime, date
import calendar
import random

# ─── Tenta importar matplotlib ────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

# ══════════════════════════════════════════════════════════════════════════════
#  BANCO DE DADOS (CORRIGIDO PARA SALVAR PERMANENTEMENTE NO PC)
# ══════════════════════════════════════════════════════════════════════════════

USER_HOME = os.path.expanduser("~")
DATA_DIR = os.path.join(USER_HOME, "GastouQuanto")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "gastou_quanto.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS categoria (
            idcategoria   INTEGER PRIMARY KEY AUTOINCREMENT,
            nomecategoria TEXT    NOT NULL,
            cor           TEXT    NOT NULL DEFAULT '#4e8ef7'
        );

        CREATE TABLE IF NOT EXISTS despesa (
            idgasto       INTEGER PRIMARY KEY AUTOINCREMENT,
            nomegasto     TEXT    NOT NULL,
            valorgasto    REAL    NOT NULL,
            datagasto     TEXT    NOT NULL,
            idcategoria   INTEGER NOT NULL,
            despesapaga   INTEGER NOT NULL DEFAULT 0,
            observacao    TEXT,
            FOREIGN KEY (idcategoria) REFERENCES categoria(idcategoria)
        );

        CREATE TABLE IF NOT EXISTS receita (
            idganho       INTEGER PRIMARY KEY AUTOINCREMENT,
            nomeganho     TEXT    NOT NULL,
            valorganho    REAL    NOT NULL,
            dataganho     TEXT    NOT NULL,
            idcategoria   INTEGER NOT NULL,
            ganhorecebido INTEGER NOT NULL DEFAULT 0,
            observacao    TEXT,
            FOREIGN KEY (idcategoria) REFERENCES categoria(idcategoria)
        );
    """)

    c.execute("SELECT COUNT(*) FROM categoria")
    if c.fetchone()[0] == 0:
        padroes = [
            ("Alimentação",  "#e74c3c"),
            ("Transporte",   "#070707"),
            ("Moradia",      "#8e44ad"),
            ("Saúde",        "#27ae60"),
            ("Lazer",        "#2980b9"),
            ("Educação",     "#16a085"),
            ("Salário",      "#2ecc71"),
            ("Investimento", "#f1c40f"),
        ]
        c.executemany(
            "INSERT INTO categoria (nomecategoria, cor) VALUES (?,?)", padroes)

    conn.commit()
    conn.close()


init_db()

# ──────────────────────────────────────────────────────────────────────────────
#  Funções de acesso ao banco
# ──────────────────────────────────────────────────────────────────────────────


def categoria_getall():
    c = get_conn().cursor()
    c.execute(
        "SELECT idcategoria, nomecategoria, cor FROM categoria ORDER BY nomecategoria")
    return c.fetchall()


def categoria_insert(nome, cor):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO categoria (nomecategoria, cor) VALUES (?,?)", (nome, cor))
    conn.commit()
    conn.close()


def categoria_update(id_, nome, cor):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE categoria SET nomecategoria=?, cor=? WHERE idcategoria=?", (nome, cor, id_))
    conn.commit()
    conn.close()


def categoria_delete(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM categoria WHERE idcategoria=?", (id_,))
    conn.commit()
    conn.close()


def despesa_getbymonthyear(month, year):
    c = get_conn().cursor()
    c.execute("""
        SELECT d.idgasto, d.nomegasto, d.valorgasto, d.datagasto,
               d.idcategoria, d.despesapaga, d.observacao, cat.nomecategoria, cat.cor
        FROM despesa d
        JOIN categoria cat ON d.idcategoria = cat.idcategoria
        WHERE strftime('%m', d.datagasto) = ?
          AND strftime('%Y', d.datagasto) = ?
        ORDER BY d.datagasto DESC
    """, (f"{month:02d}", str(year)))
    return c.fetchall()


def despesa_getgrouped(month, year):
    c = get_conn().cursor()
    c.execute("""
        SELECT cat.nomecategoria, cat.cor, SUM(d.valorgasto) as soma
        FROM despesa d
        JOIN categoria cat ON d.idcategoria = cat.idcategoria
        WHERE strftime('%m', d.datagasto) = ?
          AND strftime('%Y', d.datagasto) = ?
        GROUP BY d.idcategoria
        ORDER BY soma DESC
    """, (f"{month:02d}", str(year)))
    return c.fetchall()


def despesa_insert(nome, valor, data, idcat, paga, obs):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO despesa (nomegasto,valorgasto,datagasto,idcategoria,despesapaga,observacao) VALUES (?,?,?,?,?,?)",
              (nome, valor, data, idcat, int(paga), obs))
    conn.commit()
    conn.close()


def despesa_update(id_, nome, valor, data, idcat, paga, obs):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE despesa SET nomegasto=?,valorgasto=?,datagasto=?,idcategoria=?,despesapaga=?,observacao=? WHERE idgasto=?",
              (nome, valor, data, idcat, int(paga), obs, id_))
    conn.commit()
    conn.close()


def despesa_delete(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM despesa WHERE idgasto=?", (id_,))
    conn.commit()
    conn.close()


def receita_getbymonthyear(month, year):
    c = get_conn().cursor()
    c.execute("""
        SELECT r.idganho, r.nomeganho, r.valorganho, r.dataganho,
               r.idcategoria, r.ganhorecebido, r.observacao, cat.nomecategoria, cat.cor
        FROM receita r
        JOIN categoria cat ON r.idcategoria = cat.idcategoria
        WHERE strftime('%m', r.dataganho) = ?
          AND strftime('%Y', r.dataganho) = ?
        ORDER BY r.dataganho DESC
    """, (f"{month:02d}", str(year)))
    return c.fetchall()


def receita_getgrouped(month, year):
    c = get_conn().cursor()
    c.execute("""
        SELECT cat.nomecategoria, cat.cor, SUM(r.valorganho) as soma
        FROM receita r
        JOIN categoria cat ON r.idcategoria = cat.idcategoria
        WHERE strftime('%m', r.dataganho) = ?
          AND strftime('%Y', r.dataganho) = ?
        GROUP BY r.idcategoria
        ORDER BY soma DESC
    """, (f"{month:02d}", str(year)))
    return c.fetchall()


def receita_insert(nome, valor, data, idcat, recebida, obs):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO receita (nomeganho,valorganho,dataganho,idcategoria,ganhorecebido,observacao) VALUES (?,?,?,?,?,?)",
              (nome, valor, data, idcat, int(recebida), obs))
    conn.commit()
    conn.close()


def receita_update(id_, nome, valor, data, idcat, recebida, obs):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE receita SET nomeganho=?,valorganho=?,dataganho=?,idcategoria=?,ganhorecebido=?,observacao=? WHERE idganho=?",
              (nome, valor, data, idcat, int(recebida), obs, id_))
    conn.commit()
    conn.close()


def receita_delete(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM receita WHERE idganho=?", (id_,))
    conn.commit()
    conn.close()


def get_totais(month, year):
    c = get_conn().cursor()
    c.execute("SELECT COALESCE(SUM(valorgasto),0) FROM despesa WHERE strftime('%m',datagasto)=? AND strftime('%Y',datagasto)=?",
              (f"{month:02d}", str(year)))
    total_desp = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valorganho),0) FROM receita WHERE strftime('%m',dataganho)=? AND strftime('%Y',dataganho)=?",
              (f"{month:02d}", str(year)))
    total_rec = c.fetchone()[0]
    return total_desp, total_rec

# ══════════════════════════════════════════════════════════════════════════════
#  PALETA / ESTILOS
# ══════════════════════════════════════════════════════════════════════════════


C_PRIMARY = "#1a73e8"
C_BG = "#f5f7fa"
C_CARD = "#ffffff"
C_DESP = "#e53935"
C_REC = "#43a047"
C_SALDO_POS = "#1565c0"
C_SALDO_NEG = "#b71c1c"
C_TEXT = "#212121"
C_SUBTEXT = "#757575"
C_BORDER = "#e0e0e0"

FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_AMOUNT = ("Segoe UI", 14, "bold")

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def fmt_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def color_dot(parent, cor, size=14):
    c = tk.Canvas(parent, width=size, height=size,
                  bg=parent.cget("bg"), highlightthickness=0)
    c.create_oval(1, 1, size-1, size-1, fill=cor, outline="")
    return c

# ══════════════════════════════════════════════════════════════════════════════
#  DIALOGS
# ══════════════════════════════════════════════════════════════════════════════


class DespesaDialog(tk.Toplevel):
    def __init__(self, parent, despesa=None, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.despesa = despesa
        self.title("Alterar Despesa" if despesa else "Adicionar Despesa")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.grab_set()
        self._build()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()//2
        py = parent.winfo_rooty() + parent.winfo_height()//2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w//2}+{py - h//2}")

    def _build(self):
        pad = {"padx": 14, "pady": 5}
        tk.Label(self, text="Valor (R$) *", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_valor = tk.StringVar(
            value=f"{self.despesa[2]:.2f}".replace(".", ",") if self.despesa else "")
        tk.Entry(self, textvariable=self.val_valor,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Descrição *", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_nome = tk.StringVar(
            value=self.despesa[1] if self.despesa else "")
        tk.Entry(self, textvariable=self.val_nome,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Data * (DD/MM/AAAA)", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_data = tk.StringVar(
            value=datetime.strptime(self.despesa[3], "%Y-%m-%d").strftime(
                "%d/%m/%Y") if self.despesa else datetime.today().strftime("%d/%m/%Y")
        )
        tk.Entry(self, textvariable=self.val_data,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Categoria *", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.categorias = categoria_getall()
        self.cat_names = [c[1] for c in self.categorias]
        self.val_cat = tk.StringVar()
        combo = ttk.Combobox(self, textvariable=self.val_cat,
                             values=self.cat_names, state="readonly", width=28, font=FONT_BODY)
        combo.pack(fill="x", **pad)
        if self.despesa:
            for i, c in enumerate(self.categorias):
                if c[0] == self.despesa[4]:
                    combo.current(i)
                    break
        elif self.cat_names:
            combo.current(0)

        self.val_paga = tk.BooleanVar(value=bool(
            self.despesa[5]) if self.despesa else False)
        tk.Checkbutton(self, text="Despesa paga?", variable=self.val_paga, bg=C_BG,
                       font=FONT_BODY, fg=C_TEXT, activebackground=C_BG).pack(anchor="w", **pad)

        tk.Label(self, text="Observação", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_obs = tk.StringVar(
            value=self.despesa[6] or "" if self.despesa else "")
        tk.Entry(self, textvariable=self.val_obs,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        frm = tk.Frame(self, bg=C_BG)
        frm.pack(fill="x", padx=14, pady=12)
        tk.Button(frm, text="Cancelar", command=self.destroy, font=FONT_BODY, bg=C_BORDER,
                  fg=C_TEXT, relief="flat", cursor="hand2", padx=12).pack(side="right", padx=4)
        tk.Button(frm, text="Salvar", command=self._save, font=FONT_BODY, bg=C_PRIMARY,
                  fg="white", relief="flat", cursor="hand2", padx=12).pack(side="right")

    def _save(self):
        nome = self.val_nome.get().strip()
        data_str = self.val_data.get().strip()
        obs = self.val_obs.get().strip()
        paga = self.val_paga.get()
        cat_name = self.val_cat.get()

        if not nome:
            messagebox.showwarning(
                "Atenção", "Campos marcados com * são obrigatórios", parent=self)
            return
        try:
            valor = float(self.val_valor.get().replace(
                ",", ".").replace("R$", "").strip())
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Valor inválido.", parent=self)
            return
        try:
            data_dt = datetime.strptime(data_str, "%d/%m/%Y")
            data_db = data_dt.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Atenção", "Data inválida. Use DD/MM/AAAA.", parent=self)
            return

        idcat = None
        for c in self.categorias:
            if c[1] == cat_name:
                idcat = c[0]
                break
        if idcat is None:
            messagebox.showwarning(
                "Atenção", "Selecione uma categoria.", parent=self)
            return

        if self.despesa:
            despesa_update(self.despesa[0], nome,
                           valor, data_db, idcat, paga, obs)
        else:
            despesa_insert(nome, valor, data_db, idcat, paga, obs)

        if self.on_save:
            self.on_save()
        self.destroy()


class ReceitaDialog(tk.Toplevel):
    def __init__(self, parent, receita=None, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.receita = receita
        self.title("Alterar Receita" if receita else "Adicionar Receita")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.grab_set()
        self._build()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()//2
        py = parent.winfo_rooty() + parent.winfo_height()//2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w//2}+{py - h//2}")

    def _build(self):
        pad = {"padx": 14, "pady": 5}
        tk.Label(self, text="Valor (R$) *", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_valor = tk.StringVar(
            value=f"{self.receita[2]:.2f}".replace(".", ",") if self.receita else "")
        tk.Entry(self, textvariable=self.val_valor,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Descrição *", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_nome = tk.StringVar(
            value=self.receita[1] if self.receita else "")
        tk.Entry(self, textvariable=self.val_nome,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Data * (DD/MM/AAAA)", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_data = tk.StringVar(
            value=datetime.strptime(self.receita[3], "%Y-%m-%d").strftime(
                "%d/%m/%Y") if self.receita else datetime.today().strftime("%d/%m/%Y")
        )
        tk.Entry(self, textvariable=self.val_data,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Categoria *", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.categorias = categoria_getall()
        self.cat_names = [c[1] for c in self.categorias]
        self.val_cat = tk.StringVar()
        combo = ttk.Combobox(self, textvariable=self.val_cat,
                             values=self.cat_names, state="readonly", width=28, font=FONT_BODY)
        combo.pack(fill="x", **pad)
        if self.receita:
            for i, c in enumerate(self.categorias):
                if c[0] == self.receita[4]:
                    combo.current(i)
                    break
        elif self.cat_names:
            combo.current(0)

        self.val_rec = tk.BooleanVar(value=bool(
            self.receita[5]) if self.receita else False)
        tk.Checkbutton(self, text="Receita recebida?", variable=self.val_rec, bg=C_BG,
                       font=FONT_BODY, fg=C_TEXT, activebackground=C_BG).pack(anchor="w", **pad)

        tk.Label(self, text="Observação", font=FONT_SMALL,
                 bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_obs = tk.StringVar(
            value=self.receita[6] or "" if self.receita else "")
        tk.Entry(self, textvariable=self.val_obs,
                 font=FONT_BODY, width=30).pack(fill="x", **pad)

        frm = tk.Frame(self, bg=C_BG)
        frm.pack(fill="x", padx=14, pady=12)
        tk.Button(frm, text="Cancelar", command=self.destroy, font=FONT_BODY, bg=C_BORDER,
                  fg=C_TEXT, relief="flat", cursor="hand2", padx=12).pack(side="right", padx=4)
        tk.Button(frm, text="Salvar", command=self._save, font=FONT_BODY, bg=C_PRIMARY,
                  fg="white", relief="flat", cursor="hand2", padx=12).pack(side="right")

    def _save(self):
        nome = self.val_nome.get().strip()
        data_str = self.val_data.get().strip()
        obs = self.val_obs.get().strip()
        rec = self.val_rec.get()
        cat_name = self.val_cat.get()

        if not nome:
            messagebox.showwarning(
                "Atenção", "Campos marcados com * são obrigatórios", parent=self)
            return
        try:
            valor = float(self.val_valor.get().replace(
                ",", ".").replace("R$", "").strip())
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Valor inválido.", parent=self)
            return
        try:
            data_dt = datetime.strptime(data_str, "%d/%m/%Y")
            data_db = data_dt.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Atenção", "Data inválida. Use DD/MM/AAAA.", parent=self)
            return

        idcat = None
        for c in self.categorias:
            if c[1] == cat_name:
                idcat = c[0]
                break
        if idcat is None:
            messagebox.showwarning(
                "Atenção", "Selecione uma categoria.", parent=self)
            return

        if self.receita:
            receita_update(self.receita[0], nome,
                           valor, data_db, idcat, rec, obs)
        else:
            receita_insert(nome, valor, data_db, idcat, rec, obs)

        if self.on_save:
            self.on_save()
        self.destroy()

# ══════════════════════════════════════════════════════════════════════════════
#  ABAS E LAYOUT PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════


class CashflowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GastouQuanto - Controle Financeiro")
        self.root.geometry("1024x700")
        self.root.configure(bg=C_BG)

        self.current_month = date.today().month
        self.current_year = date.today().year

        self._build_layout()
        self.refresh()

    def _build_layout(self):
        nav_frame = tk.Frame(self.root, bg=C_PRIMARY, height=60)
        nav_frame.pack(fill="x", side="top")
        nav_frame.pack_propagate(False)

        tk.Button(nav_frame, text="◀", font=FONT_TITLE, bg=C_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", command=self.prev_month).pack(side="left", padx=20)
        self.lbl_mes_ano = tk.Label(
            nav_frame, text="", font=FONT_TITLE, bg=C_PRIMARY, fg="white")
        self.lbl_mes_ano.pack(side="left", expand=True)
        tk.Button(nav_frame, text="▶", font=FONT_TITLE, bg=C_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", command=self.next_month).pack(side="right", padx=20)

        main_content = tk.Frame(self.root, bg=C_BG)
        main_content.pack(fill="both", expand=True, padx=10, pady=10)

        left_pane = tk.Frame(main_content, bg=C_BG, width=550)
        left_pane.pack(side="left", fill="both", expand=True)

        self.right_pane = tk.Frame(
            main_content, bg=C_CARD, bd=1, relief="solid", highlightthickness=0)
        self.right_pane.configure(
            highlightbackground=C_BORDER, highlightcolor=C_BORDER)
        self.right_pane.pack(side="right", fill="both",
                             expand=True, padx=(10, 0))

        summary_frame = tk.Frame(left_pane, bg=C_BG)
        summary_frame.pack(fill="x", pady=(0, 10))

        self.card_rec = self._create_card(summary_frame, "Receitas", C_REC)
        self.card_rec.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.card_desp = self._create_card(summary_frame, "Despesas", C_DESP)
        self.card_desp.pack(side="left", fill="both", expand=True, padx=5)

        self.card_saldo = self._create_card(
            summary_frame, "Saldo Geral", C_TEXT)
        self.card_saldo.pack(side="left", fill="both",
                             expand=True, padx=(5, 0))

        self.notebook = ttk.Notebook(left_pane)
        self.notebook.pack(fill="both", expand=True)

        self.tab_despesas = tk.Frame(self.notebook, bg=C_CARD)
        self.tab_receitas = tk.Frame(self.notebook, bg=C_CARD)

        self.notebook.add(self.tab_despesas, text=" Despesas ")
        self.notebook.add(self.tab_receitas, text=" Receitas ")

        self._setup_tab_list(self.tab_despesas, "despesa")
        self._setup_tab_list(self.tab_receitas, "receita")

    def _create_card(self, parent, title, color):
        card = tk.Frame(parent, bg=C_CARD, bd=1, relief="solid", height=80)
        card.pack_propagate(False)
        tk.Label(card, text=title, font=FONT_SMALL, fg=C_SUBTEXT,
                 bg=C_CARD).pack(anchor="w", padx=10, pady=(8, 2))
        lbl_val = tk.Label(card, text="R$ 0,00",
                           font=FONT_AMOUNT, fg=color, bg=C_CARD)
        lbl_val.pack(anchor="w", padx=10)
        card.lbl_val = lbl_val
        return card

    def _setup_tab_list(self, tab, type_):
        btn_frame = tk.Frame(tab, bg=C_CARD, pady=8)
        btn_frame.pack(fill="x", padx=10)

        if type_ == "despesa":
            tk.Button(btn_frame, text="+ Nova Despesa", bg=C_DESP, fg="white", font=FONT_BODY,
                      relief="flat", cursor="hand2", command=self.add_despesa).pack(side="left")
        else:
            tk.Button(btn_frame, text="+ Nova Receita", bg=C_REC, fg="white", font=FONT_BODY,
                      relief="flat", cursor="hand2", command=self.add_receita).pack(side="left")

        tk.Button(btn_frame, text="Editar", bg=C_BG, fg=C_TEXT, font=FONT_BODY, relief="flat",
                  cursor="hand2", command=lambda: self.edit_item(type_)).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Remover", bg="#ffcdd2", fg=C_DESP, font=FONT_BODY, relief="flat",
                  cursor="hand2", command=lambda: self.delete_item(type_)).pack(side="left")

        scroll = tk.Scrollbar(tab)
        scroll.pack(side="right", fill="y")

        cols = ("Descrição", "Valor", "Data", "Categoria", "Status")
        tree = ttk.Treeview(tab, columns=cols, show="headings",
                            yscrollcommand=scroll.set, selectmode="browse")
        tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        scroll.config(command=tree.yview)

        tree.heading("Descrição", text="Descrição", anchor="w")
        tree.heading("Valor", text="Valor", anchor="e")
        tree.heading("Data", text="Data", anchor="center")
        tree.heading("Categoria", text="Categoria", anchor="w")
        tree.heading("Status", text="Status", anchor="center")

        tree.column("Descrição", width=180, anchor="w")
        tree.column("Valor", width=100, anchor="e")
        tree.column("Data", width=90, anchor="center")
        tree.column("Categoria", width=110, anchor="w")
        tree.column("Status", width=80, anchor="center")

        if type_ == "despesa":
            self.tree_desp = tree
        else:
            self.tree_rec = tree

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.refresh()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.refresh()

    def add_despesa(self): DespesaDialog(self.root, on_save=self.refresh)
    def add_receita(self): ReceitaDialog(self.root, on_save=self.refresh)

    def edit_item(self, type_):
        tree = self.tree_desp if type_ == "despesa" else self.tree_rec
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(
                "Aviso", "Selecione um item da lista para editar.")
            return
        item_id = tree.item(sel[0])['tags'][0]

        conn = get_conn()
        c = conn.cursor()
        if type_ == "despesa":
            c.execute("SELECT * FROM despesa WHERE idgasto=?", (item_id,))
            DespesaDialog(self.root, despesa=c.fetchone(),
                          on_save=self.refresh)
        else:
            c.execute("SELECT * FROM receita WHERE idganho=?", (item_id,))
            ReceitaDialog(self.root, receita=c.fetchone(),
                          on_save=self.refresh)
        conn.close()

    def delete_item(self, type_):
        tree = self.tree_desp if type_ == "despesa" else self.tree_rec
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um item para remover.")
            return
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja remover este item?"):
            item_id = tree.item(sel[0])['tags'][0]
            if type_ == "despesa":
                despesa_delete(item_id)
            else:
                receita_delete(item_id)
            self.refresh()

    def refresh(self):
        self.lbl_mes_ano.config(
            text=f"{MESES[self.current_month-1]} de {self.current_year}")
        t_desp, t_rec = get_totais(self.current_month, self.current_year)
        saldo = t_rec - t_desp

        self.card_rec.lbl_val.config(text=fmt_brl(t_rec))
        self.card_desp.lbl_val.config(text=fmt_brl(t_desp))
        self.card_saldo.lbl_val.config(text=fmt_brl(
            saldo), fg=C_SALDO_POS if saldo >= 0 else C_SALDO_NEG)

        for t in (self.tree_desp, self.tree_rec):
            for i in t.get_children():
                t.delete(i)

        for d in despesa_getbymonthyear(self.current_month, self.current_year):
            status = "Pago" if d[5] else "Pendente"
            self.tree_desp.insert("", "end", values=(d[1], fmt_brl(d[2]), datetime.strptime(
                d[3], "%Y-%m-%d").strftime("%d/%m/%Y"), d[7], status), tags=(d[0],))

        for r in receita_getbymonthyear(self.current_month, self.current_year):
            status = "Recebido" if r[5] else "Pendente"
            self.tree_rec.insert("", "end", values=(r[1], fmt_brl(r[2]), datetime.strptime(
                r[3], "%Y-%m-%d").strftime("%d/%m/%Y"), r[7], status), tags=(r[0],))

        self._render_charts()

    def _render_charts(self):
        for widget in self.right_pane.winfo_children():
            widget.destroy()

        if not MATPLOTLIB_OK:
            tk.Label(self.right_pane, text="⚠️ Instale o matplotlib para ver os gráficos:\npip install matplotlib",
                     font=FONT_BODY, bg=C_CARD, fg=C_DESP, pady=40).pack(expand=True)
            return

        dados = despesa_getgrouped(self.current_month, self.current_year)
        if not dados:
            tk.Label(self.right_pane, text="Nenhuma despesa registrada neste mês.",
                     font=FONT_BODY, bg=C_CARD, fg=C_SUBTEXT).pack(expand=True)
            return

        fig = Figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111)

        labels = [d[0] for d in dados]
        colors = [d[1] for d in dados]
        valores = [d[2] for d in dados]

        ax.pie(valores, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=140, textprops={'fontsize': 9})
        ax.set_title("Distribuição de Despesas",
                     fontsize=11, fontweight='bold', pad=10)

        canvas = FigureCanvasTkAgg(fig, master=self.right_pane)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUÇÃO DO LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = CashflowApp(root)
    root.mainloop()
