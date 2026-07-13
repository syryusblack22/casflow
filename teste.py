import tkinter as tk
from tkinter import messagebox
import os

print("Iniciando teste...")

USER_HOME = os.path.expanduser("~")
DATA_DIR = os.path.join(USER_HOME, "GastouQuantoTeste")
os.makedirs(DATA_DIR, exist_ok=True)
print(f"Pasta do banco criada em: {DATA_DIR}")

root = tk.Tk()
root.title("Teste do Sistema")
root.geometry("300x200")

label = tk.Label(root, text="Se você está vendo isso,\no Python e o Tkinter estão 100% OK!", padx=20, pady=20)
label.pack()

root.mainloop()