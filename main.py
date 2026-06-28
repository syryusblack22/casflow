"""
GastouQuanto - Controle Financeiro Pessoal
Equivalente Python do app Android original.

Dependências:
    pip install matplotlib

Uso:
    python gastou_quanto.py
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
#  BANCO DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gastou_quanto.db")

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

    # Categorias padrão se tabela vazia
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
        c.executemany("INSERT INTO categoria (nomecategoria, cor) VALUES (?,?)", padroes)

    conn.commit()
    conn.close()

# ──────────────────────────────────────────────────────────────────────────────
#  Funções de acesso ao banco
# ──────────────────────────────────────────────────────────────────────────────

def categoria_getall():
    c = get_conn().cursor()
    c.execute("SELECT idcategoria, nomecategoria, cor FROM categoria ORDER BY nomecategoria")
    return c.fetchall()

def categoria_insert(nome, cor):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO categoria (nomecategoria, cor) VALUES (?,?)", (nome, cor))
    conn.commit(); conn.close()

def categoria_update(id_, nome, cor):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE categoria SET nomecategoria=?, cor=? WHERE idcategoria=?", (nome, cor, id_))
    conn.commit(); conn.close()

def categoria_delete(id_):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM categoria WHERE idcategoria=?", (id_,))
    conn.commit(); conn.close()

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
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO despesa (nomegasto,valorgasto,datagasto,idcategoria,despesapaga,observacao) VALUES (?,?,?,?,?,?)",
              (nome, valor, data, idcat, int(paga), obs))
    conn.commit(); conn.close()

def despesa_update(id_, nome, valor, data, idcat, paga, obs):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE despesa SET nomegasto=?,valorgasto=?,datagasto=?,idcategoria=?,despesapaga=?,observacao=? WHERE idgasto=?",
              (nome, valor, data, idcat, int(paga), obs, id_))
    conn.commit(); conn.close()

def despesa_delete(id_):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM despesa WHERE idgasto=?", (id_,))
    conn.commit(); conn.close()

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
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO receita (nomeganho,valorganho,dataganho,idcategoria,ganhorecebido,observacao) VALUES (?,?,?,?,?,?)",
              (nome, valor, data, idcat, int(recebida), obs))
    conn.commit(); conn.close()

def receita_update(id_, nome, valor, data, idcat, recebida, obs):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE receita SET nomeganho=?,valorganho=?,dataganho=?,idcategoria=?,ganhorecebido=?,observacao=? WHERE idganho=?",
              (nome, valor, data, idcat, int(recebida), obs, id_))
    conn.commit(); conn.close()

def receita_delete(id_):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM receita WHERE idganho=?", (id_,))
    conn.commit(); conn.close()

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

C_PRIMARY   = "#1a73e8"
C_BG        = "#f5f7fa"
C_CARD      = "#ffffff"
C_DESP      = "#e53935"
C_REC       = "#43a047"
C_SALDO_POS = "#1565c0"
C_SALDO_NEG = "#b71c1c"
C_TEXT      = "#212121"
C_SUBTEXT   = "#757575"
C_BORDER    = "#e0e0e0"
C_TAB_ACT   = "#1a73e8"
C_TAB_INACT = "#9e9e9e"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)
FONT_AMOUNT = ("Segoe UI", 14, "bold")

MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

RANDOM_COLORS = [
    "#e74c3c","#e67e22","#f1c40f","#2ecc71","#1abc9c",
    "#3498db","#9b59b6","#34495e","#e91e63","#00bcd4"
]

def fmt_brl(valor):
    return f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def color_dot(parent, cor, size=14):
    c = tk.Canvas(parent, width=size, height=size, bg=parent.cget("bg"), highlightthickness=0)
    c.create_oval(1, 1, size-1, size-1, fill=cor, outline="")
    return c

# ══════════════════════════════════════════════════════════════════════════════
#  DIALOGS
# ══════════════════════════════════════════════════════════════════════════════

class DespesaDialog(tk.Toplevel):
    """Janela para adicionar/editar despesa."""
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
        tk.Label(self, text="Valor (R$) *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_valor = tk.StringVar(value=f"{self.despesa[2]:.2f}".replace(".",",") if self.despesa else "")
        tk.Entry(self, textvariable=self.val_valor, font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Descrição *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_nome = tk.StringVar(value=self.despesa[1] if self.despesa else "")
        tk.Entry(self, textvariable=self.val_nome, font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Data * (DD/MM/AAAA)", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_data = tk.StringVar(
            value=datetime.strptime(self.despesa[3], "%Y-%m-%d").strftime("%d/%m/%Y") if self.despesa else datetime.today().strftime("%d/%m/%Y")
        )
        tk.Entry(self, textvariable=self.val_data, font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Categoria *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.categorias = categoria_getall()
        self.cat_names = [c[1] for c in self.categorias]
        self.val_cat = tk.StringVar()
        combo = ttk.Combobox(self, textvariable=self.val_cat, values=self.cat_names,
                             state="readonly", width=28, font=FONT_BODY)
        combo.pack(fill="x", **pad)
        if self.despesa:
            for i, c in enumerate(self.categorias):
                if c[0] == self.despesa[4]:
                    combo.current(i); break
        elif self.cat_names:
            combo.current(0)

        self.val_paga = tk.BooleanVar(value=bool(self.despesa[5]) if self.despesa else False)
        tk.Checkbutton(self, text="Despesa paga?", variable=self.val_paga,
                       bg=C_BG, font=FONT_BODY, fg=C_TEXT, activebackground=C_BG).pack(anchor="w", **pad)

        tk.Label(self, text="Observação", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_obs = tk.StringVar(value=self.despesa[6] or "" if self.despesa else "")
        tk.Entry(self, textvariable=self.val_obs, font=FONT_BODY, width=30).pack(fill="x", **pad)

        frm = tk.Frame(self, bg=C_BG)
        frm.pack(fill="x", padx=14, pady=12)
        tk.Button(frm, text="Cancelar", command=self.destroy,
                  font=FONT_BODY, bg=C_BORDER, fg=C_TEXT, relief="flat",
                  cursor="hand2", padx=12).pack(side="right", padx=4)
        tk.Button(frm, text="Salvar", command=self._save,
                  font=FONT_BODY, bg=C_PRIMARY, fg="white", relief="flat",
                  cursor="hand2", padx=12).pack(side="right")

    def _save(self):
        nome  = self.val_nome.get().strip()
        data_str = self.val_data.get().strip()
        obs   = self.val_obs.get().strip()
        paga  = self.val_paga.get()
        cat_name = self.val_cat.get()

        if not nome:
            messagebox.showwarning("Atenção","Campos marcados com * são obrigatórios", parent=self); return
        try:
            valor = float(self.val_valor.get().replace(",",".").replace("R$","").strip())
            if valor <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção","Valor inválido.", parent=self); return
        try:
            data_dt = datetime.strptime(data_str, "%d/%m/%Y")
            data_db = data_dt.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Atenção","Data inválida. Use DD/MM/AAAA.", parent=self); return

        idcat = None
        for c in self.categorias:
            if c[1] == cat_name:
                idcat = c[0]; break
        if idcat is None:
            messagebox.showwarning("Atenção","Selecione uma categoria.", parent=self); return

        if self.despesa:
            despesa_update(self.despesa[0], nome, valor, data_db, idcat, paga, obs)
        else:
            despesa_insert(nome, valor, data_db, idcat, paga, obs)

        if self.on_save: self.on_save()
        self.destroy()


class ReceitaDialog(tk.Toplevel):
    """Janela para adicionar/editar receita."""
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
        tk.Label(self, text="Valor (R$) *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_valor = tk.StringVar(value=f"{self.receita[2]:.2f}".replace(".",",") if self.receita else "")
        tk.Entry(self, textvariable=self.val_valor, font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Descrição *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_nome = tk.StringVar(value=self.receita[1] if self.receita else "")
        tk.Entry(self, textvariable=self.val_nome, font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Data * (DD/MM/AAAA)", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_data = tk.StringVar(
            value=datetime.strptime(self.receita[3], "%Y-%m-%d").strftime("%d/%m/%Y") if self.receita else datetime.today().strftime("%d/%m/%Y")
        )
        tk.Entry(self, textvariable=self.val_data, font=FONT_BODY, width=30).pack(fill="x", **pad)

        tk.Label(self, text="Categoria *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.categorias = categoria_getall()
        self.cat_names = [c[1] for c in self.categorias]
        self.val_cat = tk.StringVar()
        combo = ttk.Combobox(self, textvariable=self.val_cat, values=self.cat_names,
                             state="readonly", width=28, font=FONT_BODY)
        combo.pack(fill="x", **pad)
        if self.receita:
            for i, c in enumerate(self.categorias):
                if c[0] == self.receita[4]:
                    combo.current(i); break
        elif self.cat_names:
            combo.current(0)

        self.val_rec = tk.BooleanVar(value=bool(self.receita[5]) if self.receita else False)
        tk.Checkbutton(self, text="Receita recebida?", variable=self.val_rec,
                       bg=C_BG, font=FONT_BODY, fg=C_TEXT, activebackground=C_BG).pack(anchor="w", **pad)

        tk.Label(self, text="Observação", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_obs = tk.StringVar(value=self.receita[6] or "" if self.receita else "")
        tk.Entry(self, textvariable=self.val_obs, font=FONT_BODY, width=30).pack(fill="x", **pad)

        frm = tk.Frame(self, bg=C_BG)
        frm.pack(fill="x", padx=14, pady=12)
        tk.Button(frm, text="Cancelar", command=self.destroy,
                  font=FONT_BODY, bg=C_BORDER, fg=C_TEXT, relief="flat",
                  cursor="hand2", padx=12).pack(side="right", padx=4)
        tk.Button(frm, text="Salvar", command=self._save,
                  font=FONT_BODY, bg=C_PRIMARY, fg="white", relief="flat",
                  cursor="hand2", padx=12).pack(side="right")

    def _save(self):
        nome  = self.val_nome.get().strip()
        data_str = self.val_data.get().strip()
        obs   = self.val_obs.get().strip()
        rec   = self.val_rec.get()
        cat_name = self.val_cat.get()

        if not nome:
            messagebox.showwarning("Atenção","Campos marcados com * são obrigatórios", parent=self); return
        try:
            valor = float(self.val_valor.get().replace(",",".").replace("R$","").strip())
            if valor <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção","Valor inválido.", parent=self); return
        try:
            data_dt = datetime.strptime(data_str, "%d/%m/%Y")
            data_db = data_dt.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Atenção","Data inválida. Use DD/MM/AAAA.", parent=self); return

        idcat = None
        for c in self.categorias:
            if c[1] == cat_name:
                idcat = c[0]; break
        if idcat is None:
            messagebox.showwarning("Atenção","Selecione uma categoria.", parent=self); return

        if self.receita:
            receita_update(self.receita[0], nome, valor, data_db, idcat, rec, obs)
        else:
            receita_insert(nome, valor, data_db, idcat, rec, obs)

        if self.on_save: self.on_save()
        self.destroy()


class CategoriaDialog(tk.Toplevel):
    """Janela para adicionar/editar categoria."""
    def __init__(self, parent, categoria=None, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.categoria = categoria
        self.selected_color = categoria[2] if categoria else random.choice(RANDOM_COLORS)
        self.title("Alterar Categoria" if categoria else "Nova Categoria")
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
        tk.Label(self, text="Nome da Categoria *", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        self.val_nome = tk.StringVar(value=self.categoria[1] if self.categoria else "")
        tk.Entry(self, textvariable=self.val_nome, font=FONT_BODY, width=28).pack(fill="x", **pad)

        tk.Label(self, text="Cor", font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(anchor="w", **pad)
        frm_cores = tk.Frame(self, bg=C_BG)
        frm_cores.pack(fill="x", padx=14, pady=4)
        self.dot_preview = tk.Canvas(frm_cores, width=22, height=22, bg=C_BG, highlightthickness=0)
        self.dot_preview.pack(side="left", padx=(0,8))
        self._draw_dot()
        for cor in RANDOM_COLORS:
            btn = tk.Canvas(frm_cores, width=20, height=20, bg=C_BG, highlightthickness=0, cursor="hand2")
            btn.create_oval(2, 2, 18, 18, fill=cor, outline="")
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, c=cor: self._pick_color(c))

        frm = tk.Frame(self, bg=C_BG)
        frm.pack(fill="x", padx=14, pady=12)
        if self.categoria:
            tk.Button(frm, text="Excluir", command=self._delete,
                      font=FONT_BODY, bg=C_DESP, fg="white", relief="flat",
                      cursor="hand2", padx=10).pack(side="left")
        tk.Button(frm, text="Cancelar", command=self.destroy,
                  font=FONT_BODY, bg=C_BORDER, fg=C_TEXT, relief="flat",
                  cursor="hand2", padx=12).pack(side="right", padx=4)
        tk.Button(frm, text="Salvar", command=self._save,
                  font=FONT_BODY, bg=C_PRIMARY, fg="white", relief="flat",
                  cursor="hand2", padx=12).pack(side="right")

    def _draw_dot(self):
        self.dot_preview.delete("all")
        self.dot_preview.create_oval(2, 2, 20, 20, fill=self.selected_color, outline="")

    def _pick_color(self, cor):
        self.selected_color = cor
        self._draw_dot()

    def _save(self):
        nome = self.val_nome.get().strip()
        if not nome:
            messagebox.showwarning("Atenção","Nome é obrigatório.", parent=self); return
        if self.categoria:
            categoria_update(self.categoria[0], nome, self.selected_color)
        else:
            categoria_insert(nome, self.selected_color)
        if self.on_save: self.on_save()
        self.destroy()

    def _delete(self):
        if messagebox.askyesno("Confirmar","Excluir esta categoria?", parent=self):
            try:
                categoria_delete(self.categoria[0])
                if self.on_save: self.on_save()
                self.destroy()
            except Exception:
                messagebox.showerror("Erro","Não é possível excluir: categoria em uso.", parent=self)


# ══════════════════════════════════════════════════════════════════════════════
#  ABAS (FRAMES)
# ══════════════════════════════════════════════════════════════════════════════

class NavBar(tk.Frame):
    """Barra superior com mês/ano e setas de navegação."""
    def __init__(self, parent, date_state, on_change, title="", **kw):
        super().__init__(parent, bg=C_PRIMARY, **kw)
        self.date_state = date_state
        self.on_change  = on_change
        tk.Label(self, text=title, font=FONT_TITLE, bg=C_PRIMARY, fg="white").pack(side="left", padx=14)
        tk.Button(self, text="▶", font=FONT_BODY, bg=C_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", command=self._forward,
                  activebackground="#1565c0", activeforeground="white").pack(side="right", padx=8)
        self.lbl_date = tk.Label(self, font=FONT_BODY, bg=C_PRIMARY, fg="white")
        self.lbl_date.pack(side="right")
        tk.Button(self, text="◀", font=FONT_BODY, bg=C_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", command=self._back,
                  activebackground="#1565c0", activeforeground="white").pack(side="right", padx=8)
        self._update_label()

    def _update_label(self):
        m, y = self.date_state["month"], self.date_state["year"]
        self.lbl_date.config(text=f"{MESES[m-1]} / {y}")

    def _back(self):
        m, y = self.date_state["month"], self.date_state["year"]
        if m == 1: self.date_state["month"], self.date_state["year"] = 12, y - 1
        else:      self.date_state["month"] = m - 1
        self._update_label(); self.on_change()

    def _forward(self):
        m, y = self.date_state["month"], self.date_state["year"]
        if m == 12: self.date_state["month"], self.date_state["year"] = 1, y + 1
        else:        self.date_state["month"] = m + 1
        self._update_label(); self.on_change()


class ResumoFrame(tk.Frame):
    def __init__(self, parent, date_state, **kw):
        super().__init__(parent, bg=C_BG, **kw)
        self.date_state = date_state
        self.nav = NavBar(self, date_state, self.refresh, title="Resumo")
        self.nav.pack(fill="x", pady=(0,0))
        self.body = tk.Frame(self, bg=C_BG)
        self.body.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        for w in self.body.winfo_children(): w.destroy()
        m, y = self.date_state["month"], self.date_state["year"]
        total_d, total_r = get_totais(m, y)
        saldo = total_r - total_d
        saldo_cor = C_SALDO_POS if saldo >= 0 else C_SALDO_NEG

        card = tk.Frame(self.body, bg=C_CARD, bd=0, relief="flat",
                        highlightthickness=1, highlightbackground=C_BORDER)
        card.pack(padx=30, pady=30, fill="x")

        def row(label, value, color):
            f = tk.Frame(card, bg=C_CARD)
            f.pack(fill="x", padx=24, pady=10)
            tk.Label(f, text=label, font=FONT_BODY, bg=C_CARD, fg=C_SUBTEXT).pack(side="left")
            tk.Label(f, text=fmt_brl(value), font=FONT_AMOUNT, bg=C_CARD, fg=color).pack(side="right")
            tk.Frame(card, height=1, bg=C_BORDER).pack(fill="x", padx=24)

        row("💸  Despesas",  total_d, C_DESP)
        row("💰  Receitas",  total_r, C_REC)
        row("📊  Saldo",     saldo,   saldo_cor)

        # Barra visual proporcional
        if total_r > 0 or total_d > 0:
            total_max = max(total_d, total_r, 1)
            bar_frame = tk.Frame(card, bg=C_CARD)
            bar_frame.pack(fill="x", padx=24, pady=(0,20))
            tk.Label(bar_frame, text="Receitas vs Despesas", font=FONT_SMALL,
                     bg=C_CARD, fg=C_SUBTEXT).pack(anchor="w")
            canvas = tk.Canvas(bar_frame, height=20, bg=C_BORDER,
                               highlightthickness=0, relief="flat")
            canvas.pack(fill="x", pady=4)
            canvas.update_idletasks()
            def draw_bars(event=None):
                w = canvas.winfo_width()
                canvas.delete("all")
                canvas.create_rectangle(0, 0, w * (total_d / total_max), 20,
                                        fill=C_DESP, outline="")
                canvas.create_rectangle(0, 0, w * (total_r / total_max), 10,
                                        fill=C_REC, outline="")
            canvas.bind("<Configure>", draw_bars)
            self.after(50, draw_bars)


class ListaFrame(tk.Frame):
    """Base para abas Despesas e Receitas."""
    def __init__(self, parent, date_state, tipo, **kw):
        super().__init__(parent, bg=C_BG, **kw)
        self.date_state = date_state
        self.tipo = tipo  # "despesa" ou "receita"
        label = "Despesas" if tipo == "despesa" else "Receitas"
        self.nav = NavBar(self, date_state, self.refresh, title=label)
        self.nav.pack(fill="x")

        # Scrollable list
        container = tk.Frame(self, bg=C_BG)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg=C_BG, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=C_BG)
        self.window_id = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window_id, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Botão adicionar
        cor_btn = C_DESP if tipo == "despesa" else C_REC
        add_label = "＋ Adicionar Despesa" if tipo == "despesa" else "＋ Adicionar Receita"
        tk.Button(self, text=add_label, font=FONT_BODY, bg=cor_btn, fg="white",
                  relief="flat", cursor="hand2", pady=8, command=self._add).pack(fill="x", padx=20, pady=10)

        self.refresh()

    def _add(self):
        if self.tipo == "despesa":
            DespesaDialog(self.winfo_toplevel(), on_save=self.refresh)
        else:
            ReceitaDialog(self.winfo_toplevel(), on_save=self.refresh)

    def refresh(self):
        for w in self.inner.winfo_children(): w.destroy()
        m, y = self.date_state["month"], self.date_state["year"]
        if self.tipo == "despesa":
            rows = despesa_getbymonthyear(m, y)
        else:
            rows = receita_getbymonthyear(m, y)

        if not rows:
            tk.Label(self.inner, text="Não há dados para serem mostrados.",
                     font=FONT_BODY, bg=C_BG, fg=C_SUBTEXT).pack(pady=40)
            return

        for row in rows:
            self._row_widget(row)

    def _row_widget(self, row):
        # row layout: id, nome, valor, data, idcat, flag, obs, catNome, catCor
        id_     = row[0]
        nome    = row[1]
        valor   = row[2]
        data    = datetime.strptime(row[3], "%Y-%m-%d").strftime("%d/%m/%Y")
        flag    = bool(row[5])
        cat_nome = row[7]
        cat_cor  = row[8]

        card = tk.Frame(self.inner, bg=C_CARD, cursor="hand2",
                        highlightthickness=1, highlightbackground=C_BORDER)
        card.pack(fill="x", padx=14, pady=4)
        card.bind("<Button-1>", lambda e, r=row: self._edit(r))

        left = tk.Frame(card, bg=C_CARD)
        left.pack(side="left", padx=10, pady=8, fill="y", expand=True)
        color_dot(left, cat_cor, 12).pack(side="left", padx=(0,6))
        info = tk.Frame(left, bg=C_CARD)
        info.pack(side="left")
        tk.Label(info, text=nome, font=FONT_BODY, bg=C_CARD, fg=C_TEXT,
                 anchor="w").pack(anchor="w")
        sub = f"{data}  •  {cat_nome}"
        if flag:
            sub += "  ✓"
        tk.Label(info, text=sub, font=FONT_SMALL, bg=C_CARD, fg=C_SUBTEXT,
                 anchor="w").pack(anchor="w")

        cor_valor = C_REC if self.tipo == "receita" else C_DESP
        tk.Label(card, text=fmt_brl(valor), font=FONT_AMOUNT, bg=C_CARD,
                 fg=cor_valor).pack(side="right", padx=14)

    def _edit(self, row):
        if self.tipo == "despesa":
            DespesaDialog(self.winfo_toplevel(), despesa=row, on_save=self.refresh)
        else:
            ReceitaDialog(self.winfo_toplevel(), receita=row, on_save=self.refresh)


class DashboardFrame(tk.Frame):
    def __init__(self, parent, date_state, **kw):
        super().__init__(parent, bg=C_BG, **kw)
        self.date_state = date_state
        self.nav = NavBar(self, date_state, self.refresh, title="Dashboards")
        self.nav.pack(fill="x")

        if not MATPLOTLIB_OK:
            tk.Label(self, text="⚠  Instale matplotlib para ver os gráficos:\n\npip install matplotlib",
                     font=FONT_BODY, bg=C_BG, fg=C_SUBTEXT, justify="center").pack(expand=True)
            return

        self.body = tk.Frame(self, bg=C_BG)
        self.body.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        if not MATPLOTLIB_OK: return
        for w in self.body.winfo_children(): w.destroy()
        m, y = self.date_state["month"], self.date_state["year"]
        self._build_chart(despesa_getgrouped(m, y), "Despesas por Categoria")
        self._build_chart(receita_getgrouped(m, y), "Receitas por Categoria")

    def _build_chart(self, data, title):
        frame = tk.Frame(self.body, bg=C_BG)
        frame.pack(fill="both", expand=True, padx=10, pady=6)

        tk.Label(frame, text=title, font=FONT_TITLE, bg=C_BG, fg=C_TEXT).pack()

        if not data:
            tk.Label(frame, text="Sem dados neste período.",
                     font=FONT_SMALL, bg=C_BG, fg=C_SUBTEXT).pack(pady=10)
            return

        labels = [r[0] for r in data]
        sizes  = [r[2] for r in data]
        colors = [r[1] for r in data]

        fig = Figure(figsize=(4, 2.6), dpi=90, facecolor=C_BG)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(C_BG)
        wedges, _ = ax.pie(sizes, colors=colors, startangle=90,
                           wedgeprops={"linewidth": 1, "edgecolor": "white"})
        ax.axis("equal")

        # Legenda lateral
        total = sum(sizes)
        legend_labels = [f"{l}  {fmt_brl(s)}  ({100*s/total:.0f}%)" for l, s in zip(labels, sizes)]
        ax.legend(wedges, legend_labels, loc="center left",
                  bbox_to_anchor=(1.02, 0.5), fontsize=7, frameon=False)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


class CategoriasFrame(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C_BG, **kw)
        header = tk.Frame(self, bg=C_PRIMARY)
        header.pack(fill="x")
        tk.Label(header, text="Categorias", font=FONT_TITLE, bg=C_PRIMARY, fg="white").pack(side="left", padx=14, pady=10)
        tk.Button(header, text="＋ Nova", font=FONT_SMALL, bg="white", fg=C_PRIMARY,
                  relief="flat", cursor="hand2", command=self._add).pack(side="right", padx=14)

        container = tk.Frame(self, bg=C_BG)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg=C_BG, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=C_BG)
        self.window_id = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window_id, width=e.width))

        self.refresh()

    def _add(self):
        CategoriaDialog(self.winfo_toplevel(), on_save=self.refresh)

    def refresh(self):
        for w in self.inner.winfo_children(): w.destroy()
        for cat in categoria_getall():
            self._row(cat)

    def _row(self, cat):
        card = tk.Frame(self.inner, bg=C_CARD, cursor="hand2",
                        highlightthickness=1, highlightbackground=C_BORDER)
        card.pack(fill="x", padx=14, pady=3)
        card.bind("<Button-1>", lambda e, c=cat: self._edit(c))

        color_dot(card, cat[2], 16).pack(side="left", padx=10, pady=10)
        tk.Label(card, text=cat[1], font=FONT_BODY, bg=C_CARD, fg=C_TEXT,
                 anchor="w").pack(side="left", fill="x", expand=True)
        tk.Label(card, text="›", font=("Segoe UI", 14), bg=C_CARD,
                 fg=C_SUBTEXT).pack(side="right", padx=12)

    def _edit(self, cat):
        CategoriaDialog(self.winfo_toplevel(), categoria=cat, on_save=self.refresh)


# ══════════════════════════════════════════════════════════════════════════════
#  JANELA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GastouQuanto")
        self.geometry("480x700")
        self.minsize(420, 560)
        self.configure(bg=C_BG)

        self.date_state = {
            "month": datetime.today().month,
            "year":  datetime.today().year,
        }

        self._build_tabs()

    def _build_tabs(self):
        # Tab bar
        tab_bar = tk.Frame(self, bg=C_CARD,
                           highlightthickness=1, highlightbackground=C_BORDER)
        tab_bar.pack(side="bottom", fill="x")

        self.content = tk.Frame(self, bg=C_BG)
        self.content.pack(fill="both", expand=True)

        TABS = [
            ("🏠", "Resumo"),
            ("↓",  "Despesas"),
            ("↑",  "Receitas"),
            ("📊", "Dashboards"),
            ("🏷", "Categorias"),
        ]

        self.tab_frames = []
        self.tab_btns   = []
        self.active_tab = tk.IntVar(value=0)

        # Cria frames
        self.tab_frames.append(ResumoFrame(self.content, self.date_state))
        self.tab_frames.append(ListaFrame(self.content, self.date_state, "despesa"))
        self.tab_frames.append(ListaFrame(self.content, self.date_state, "receita"))
        self.tab_frames.append(DashboardFrame(self.content, self.date_state))
        self.tab_frames.append(CategoriasFrame(self.content))

        for i, (icon, label) in enumerate(TABS):
            col = tk.Frame(tab_bar, bg=C_CARD)
            col.pack(side="left", expand=True, fill="x")
            ico = tk.Label(col, text=icon, font=("Segoe UI", 14), bg=C_CARD, cursor="hand2")
            ico.pack()
            lbl = tk.Label(col, text=label, font=FONT_SMALL, bg=C_CARD, cursor="hand2")
            lbl.pack()
            for w in (col, ico, lbl):
                w.bind("<Button-1>", lambda e, idx=i: self._switch(idx))
            self.tab_btns.append((col, ico, lbl))

        self._switch(0)

    def _switch(self, idx):
        self.active_tab.set(idx)
        for i, frame in enumerate(self.tab_frames):
            if i == idx:
                frame.place(relwidth=1, relheight=1)
                frame.lift()
                if hasattr(frame, "refresh"):
                    frame.refresh()
            else:
                frame.place_forget()

        for i, (col, ico, lbl) in enumerate(self.tab_btns):
            fg = C_TAB_ACT if i == idx else C_TAB_INACT
            col.config(bg=C_CARD)
            ico.config(fg=fg, bg=C_CARD)
            lbl.config(fg=fg, bg=C_CARD)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
