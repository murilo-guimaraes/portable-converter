import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import subprocess
import threading
import re
import time

# --- SELETOR ORGANIZADO POR CATEGORIAS (ESTILIZADO) ---
class SeletorFormatos(tk.Toplevel):
    def __init__(self, parent, categorias, callback, x, y):
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.callback = callback
        self.categorias = categorias
        
        self.bg_color = "#2d2d2d"
        self.accent_color = "#0078d4"
        self.configure(bg=self.bg_color, highlightthickness=1, highlightbackground="#444")
        
        largura = 525
        altura = 260
        self.geometry(f"{largura}x{altura}+{x-126}+{y-(altura+25)}") 

        self.sidebar = tk.Frame(self, bg="#252525", width=170)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.container_dir = tk.Frame(self, bg=self.bg_color)
        self.container_dir.pack(side="right", fill="both", expand=True, padx=25, pady=25)

        self.criar_menu_lateral()
        self.mostrar_categoria("Vídeo")
        
        self.deiconify()
        self.focus_force()
        self.bind("<FocusOut>", lambda e: self._verificar_foco())

    def _verificar_foco(self):
        if self.focus_get() is None:
            self.destroy()

    def criar_menu_lateral(self):
        icones = {"Vídeo": "🎬", "Imagem": "🎴", "Áudio": "🎵", "Documentos": "📄"}
        for cat in self.categorias.keys():
            # Verifica se é a categoria Documentos para inserir o selo BETA
            if cat == "Documentos":
                beta_label = tk.Label(self.sidebar, text="BETA", bg="#252525", fg="#00aaff",
                                     font=("Segoe UI Variable Text", 8, "bold italic"))
                beta_label.pack(anchor="w", padx=15, pady=(10, 0)) # Um pequeno recuo para alinhar

            txt = f"{icones.get(cat, '')} {cat.upper()}"
            btn = tk.Button(self.sidebar, text=txt, bg="#252525", fg="#aaa",
                            font=("Segoe UI Variable Text", 12, "bold"), bd=0, 
                            pady=15 if cat == "Documentos" else 20, # Reduz o pady se tiver o selo em cima
                            cursor="hand2", anchor="w", padx=15,
                            activebackground=self.accent_color, activeforeground="white", 
                            relief="flat", command=lambda c=cat: self.mostrar_categoria(c))
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#333", fg="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#252525", fg="#aaa"))

    def mostrar_categoria(self, nome_cat):
        for widget in self.container_dir.winfo_children():
            widget.destroy()

        ttk.Label(self.container_dir, text=f"FORMATOS DE {nome_cat.upper()}", 
                  font=("Segoe UI Variable Display", 13, "bold"), foreground=self.accent_color).pack(pady=(0, 10), anchor="w")
        
        frame_grid = tk.Frame(self.container_dir, bg=self.bg_color)
        frame_grid.pack(fill="both", expand=True)

        formatos = self.categorias[nome_cat]
        for i, fmt in enumerate(formatos):
            btn = ttk.Button(frame_grid, text=fmt, width=8, command=lambda f=fmt: self.selecionar(f))
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=10)

    def selecionar(self, formato):
        self.callback(formato)
        self.after(10, self.destroy)

# --- CLASSE PRINCIPAL ---
class Main:
    def __init__(self, root):
        self.root = root
        self.root.title("Portable Converter | Build 19.4.26")
        self.root.geometry("1050x900") 

        self.ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffmpeg.exe")

        # --- CARREGAR TEMA AZURE ---
        try:
            caminho_tema = os.path.join(os.path.dirname(__file__), "azure", "azure.tcl")
            self.root.tk.call("source", caminho_tema)
            self.root.tk.call("set_theme", "dark")
        except: pass

        self.arquivos_data = []
        self.formato_alvo = tk.StringVar(value="MP4")
        self.preset_conversao = tk.StringVar(value="medium") 
        self.max_paralelos = tk.IntVar(value=1)
        
        # --- CONTROLES DE ESTADO ---
        self.esta_convertendo = False 
        self.cancelar_solicitado = False
        self.pausado = False
        self.event_pausa = threading.Event()
        self.event_pausa.set() # Começa permitindo a execução
        
        self.categorias_formatos = {
            "Vídeo": ["MP4", "AVI", "MKV", "MOV", "WEBM"],
            "Imagem": ["PNG", "JPG", "WEBP", "ICO", "BMP", "TIFF"],
            "Áudio": ["MP3", "WAV", "OGG", "FLAC"],
            "Documentos": ["PDF", "DOCX", "TXT"]
        }
        
        self.criar_ui()

    def criar_ui(self):
        self.main_container = ttk.Frame(self.root, padding=30)
        self.main_container.pack(fill="both", expand=True)

        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill="x", pady=(0, 25))

        ttk.Label(header_frame, text="Conversor Multimídia", 
                  font=("Segoe UI Variable Display", 28, "bold")).pack(side=tk.LEFT)
        
        self.btn_add = ttk.Button(header_frame, text="➕ Adicionar Arquivos", style="Accent.TButton", 
                                  command=self.importar, takefocus=False)
        self.btn_add.pack(side=tk.RIGHT)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI Variable Text", 11), rowheight=38)
        style.configure("Treeview.Heading", font=("Segoe UI Variable Text", 11, "bold"))

        self.tree = ttk.Treeview(self.main_container, columns=("arquivo", "tamanho", "tipo", "status"), 
                                 show="headings", height=12)
        self.tree.heading("arquivo", text=" Arquivo")
        self.tree.heading("tamanho", text=" Tamanho")
        self.tree.heading("tipo", text=" Formato")
        self.tree.heading("status", text=" Status")
        
        self.tree.column("arquivo", width=400)
        self.tree.column("tamanho", width=120, anchor="center")
        self.tree.column("tipo", width=120, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.tag_configure("processando", foreground="#00aaff")
        self.tree.tag_configure("concluido", foreground="#00ff7f")
        self.tree.tag_configure("erro", foreground="#ff4d4d")

        self.placeholder = ttk.Label(self.tree, text="Arraste e solte seus arquivos aqui", 
                                     font=("Segoe UI Variable Text", 16), foreground="#666")
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

        footer_frame = ttk.Frame(self.main_container)
        footer_frame.pack(fill="x", pady=(25, 0))

        self.dest_frame = ttk.LabelFrame(footer_frame, text=" Saída ", padding=15)
        self.dest_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 10))
        
        ttk.Label(self.dest_frame, text="Converter para:", font=("Segoe UI Variable Text", 11)).pack(side=tk.LEFT, padx=(0, 15))
        self.btn_seletor = ttk.Button(self.dest_frame, text=self.formato_alvo.get(), width=15, 
                                      command=self.abrir_seletor, takefocus=False)
        self.btn_seletor.pack(side=tk.LEFT)

        self.mode_frame = ttk.LabelFrame(footer_frame, text=" Modo e Performance ", padding=15)
        self.mode_frame.pack(side=tk.LEFT, fill="both", expand=True)
        
        modos = [("⚡ Velocidade", "ultrafast"), ("⚖ Balanceado", "medium"), ("⭐ Qualidade", "slower")]
        for text, mode in modos:
            ttk.Radiobutton(self.mode_frame, text=text, variable=self.preset_conversao, value=mode, takefocus=False).pack(side=tk.LEFT, padx=10)

        self.separador_performance = ttk.Separator(self.mode_frame, orient="vertical")
        self.separador_performance.pack(side=tk.LEFT, fill="y", padx=15)
        
        self.lbl_fila = ttk.Label(self.mode_frame, text="Fila:", font=("Segoe UI Variable Text", 11), takefocus=False)
        self.lbl_fila.pack(side=tk.LEFT)
        
        # --- PARTE DO COMBOBOX SEM HIGHLIGHT ---

        self.combo_paralelo = ttk.Combobox(
            self.mode_frame, 
            values=[1, 2, 3, 4], 
            textvariable=self.max_paralelos,
            width=3, 
            font=("Segoe UI Variable Text", 11), 
            state="readonly", 
            takefocus=False  # Impede que o tab pare nele
        )
        self.combo_paralelo.pack(side=tk.LEFT, padx=5)

        # Limpa a seleção azul assim que o usuário clica ou seleciona um número
        self.combo_paralelo.bind("<<ComboboxSelected>>", lambda e: self.combo_paralelo.selection_clear())
        self.combo_paralelo.bind("<FocusIn>", lambda e: self.combo_paralelo.selection_clear())
        
        self.lbl_vez = ttk.Label(self.mode_frame, text="por vez", font=("Segoe UI Variable Text", 11), takefocus=False)
        self.lbl_vez.pack(side=tk.LEFT)

        self.status_label = ttk.Label(self.main_container, text="Pronto para começar", font=("Segoe UI Variable Text", 11))
        self.status_label.pack(fill="x", pady=(20, 5))
        
        self.progress_bar = ttk.Progressbar(self.main_container, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 25))

        self.action_frame = ttk.Frame(self.main_container)
        self.action_frame.pack(fill="x")
        
        self.btn_remover = ttk.Button(self.action_frame, text="❌ Remover Selecionado", command=self.remover_item, takefocus=False)
        self.btn_remover.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_limpar = ttk.Button(self.action_frame, text="🧹 Limpar Tudo", command=self.resetar, takefocus=False)
        self.btn_limpar.pack(side=tk.LEFT)
        
        # Botão CANCELAR (Inicia oculto)
        self.btn_cancelar = ttk.Button(self.action_frame, text="CANCELAR", command=self.solicitar_cancelamento, takefocus=False)
        
        self.btn_conv = ttk.Button(self.action_frame, text="INICIAR CONVERSÃO", style="Accent.TButton", 
                                   width=25, command=self.alternar_conversao, takefocus=False)
        self.btn_conv.pack(side=tk.RIGHT)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.processar_drop)

    def abrir_seletor(self):
        if self.esta_convertendo: return
        x, y = self.btn_seletor.winfo_rootx(), self.btn_seletor.winfo_rooty()
        SeletorFormatos(self.root, self.categorias_formatos, self.atualizar_formato, x, y)

    def atualizar_formato(self, novo_fmt):
        self.formato_alvo.set(novo_fmt)
        self.btn_seletor.config(text=novo_fmt)

    def formatar_tamanho(self, caminho):
        tamanho_bytes = os.path.getsize(caminho)
        for unidade in ['B', 'KB', 'MB', 'GB']:
            if tamanho_bytes < 1024: return f"{tamanho_bytes:.1f} {unidade}"
            tamanho_bytes /= 1024
        return f"{tamanho_bytes:.1f} TB"

    def gerenciar_arquivos(self, caminhos):
        if self.esta_convertendo: return
        exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.mp3', '.wav', '.ogg', '.flac', '.mp4', '.mkv', '.avi', '.mov', '.webm', '.pdf', '.docx', '.txt')
        for p in caminhos:
            if p.lower().endswith(exts) and not any(d['path'] == p for d in self.arquivos_data):
                nome = os.path.basename(p)
                ext = os.path.splitext(p)[1].upper()
                tamanho = self.formatar_tamanho(p)
                self.arquivos_data.append({'path': p, 'nome': nome, 'tamanho': tamanho})
                self.tree.insert("", "end", values=(nome, tamanho, ext, "Pronto"))
        if self.arquivos_data: self.placeholder.place_forget()

    def importar(self):
        self.gerenciar_arquivos(filedialog.askopenfilenames())

    def processar_drop(self, event):
        self.gerenciar_arquivos(self.root.tk.splitlist(event.data))

    def remover_item(self):
        selecionados = self.tree.selection()
        for item in selecionados:
            idx = self.tree.index(item)
            self.arquivos_data.pop(idx)
            self.tree.delete(item)
        if not self.arquivos_data: self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def resetar(self):
        self.arquivos_data.clear()
        for i in self.tree.get_children(): self.tree.delete(i)
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def alternar_conversao(self):
        if not self.esta_convertendo:
            self.iniciar_conversao()
        else:
            if self.pausado:
                self.pausado = False
                self.event_pausa.set()
                self.btn_conv.config(text="PAUSAR")
                self.status_label.config(text="Resumindo conversão...")
            else:
                self.pausado = True
                self.event_pausa.clear()
                self.btn_conv.config(text="RETOMAR")
                self.status_label.config(text="Conversão pausada.")

    def solicitar_cancelamento(self):
        if messagebox.askyesno("Cancelar", "Deseja interromper todo o processamento?"):
            self.cancelar_solicitado = True
            self.event_pausa.set() # Garante que as threads acordem se estiverem pausadas

    def iniciar_conversao(self):
        if not self.arquivos_data: return
        pasta = filedialog.askdirectory()
        if not pasta: return
        
        self.esta_convertendo = True
        self.cancelar_solicitado = False
        self.pausado = False
        self.event_pausa.set()
        
        # UI State - Bloquear e trocar botões
        self.btn_conv.config(text="PAUSAR")
        self.btn_cancelar.pack(side=tk.RIGHT, padx=10)
        self.btn_add.config(state="disabled")
        self.btn_remover.config(state="disabled")
        self.btn_limpar.config(state="disabled")
        self.btn_seletor.config(state="disabled")
        self.combo_paralelo.config(state="disabled")
        
        self.progress_bar["value"] = 0
        threading.Thread(target=self.executar, args=(pasta,), daemon=True).start()

    def executar(self, pasta_base):
        saida_dir = os.path.join(pasta_base, "Convertidos")
        os.makedirs(saida_dir, exist_ok=True)
        fmt_alvo = self.formato_alvo.get().lower()
        preset_alvo = self.preset_conversao.get()
        limite = self.max_paralelos.get()
        semaforo = threading.BoundedSemaphore(limite)
        
        num_arquivos = len(self.tree.get_children())
        arquivos_concluidos = 0
        threads_em_andamento = []

        def atualizar_status_live(porcentagem, nome, tempo_restante=None):
            progresso_total = (arquivos_concluidos / num_arquivos * 100) + (porcentagem / num_arquivos)
            self.root.after(0, lambda: self.progress_bar.configure(value=progresso_total))
            
            msg = f"⏳ Convertendo: {nome} ({porcentagem:.1f}%)"
            if tempo_restante:
                mins, segs = divmod(int(tempo_restante), 60)
                msg += f" | Restam aprox. {mins:02d}:{segs:02d}"
            self.root.after(0, lambda: self.status_label.config(text=msg))

        def processar_item(item_id, dados):
            nonlocal arquivos_concluidos
            with semaforo:
                if self.cancelar_solicitado: return
                
                caminho_origem = dados['path']
                nome_arquivo = dados['nome']
                tamanho = dados['tamanho']
                ext_origem = os.path.splitext(caminho_origem)[1].lower()

                self.root.after(0, lambda: self.tree.item(item_id, values=(nome_arquivo, tamanho, "...", "Processando..."), tags=("processando",)))
                p_saida = os.path.join(saida_dir, f"{os.path.splitext(nome_arquivo)[0]}.{fmt_alvo}")
                sucesso = False

                formatos_doc = ['pdf', 'txt', 'docx']
                formatos_pillow = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'ico']

                # --- MOTOR DE DOCUMENTOS (CORRIGIDO) ---
                try:
                    # Se a origem ou o destino for um formato de documento
                    if ext_origem[1:] in ['pdf', 'docx', 'txt'] or fmt_alvo in ['pdf', 'docx', 'txt']:
                        
                        # 1. PDF para DOCX (Usa pdf2docx)
                        if ext_origem == ".pdf" and fmt_alvo == "docx":
                            from pdf2docx import Converter
                            self.event_pausa.wait() # Respeita o botão de Pausa
                            cv = Converter(caminho_origem)
                            cv.convert(p_saida)
                            cv.close()
                            sucesso = True
                        
                        # 2. PDF para TXT (Usa PyMuPDF)
                        elif ext_origem == ".pdf" and fmt_alvo == "txt":
                            import fitz
                            doc = fitz.open(caminho_origem)
                            texto = ""
                            for pagina in doc:
                                self.event_pausa.wait()
                                if self.cancelar_solicitado: break
                                texto += pagina.get_text()
                            
                            with open(p_saida, "w", encoding="utf-8") as f:
                                f.write(texto)
                            doc.close()
                            sucesso = not self.cancelar_solicitado

                        # 3. TXT para PDF (Usa PyMuPDF)
                        elif ext_origem == ".txt" and fmt_alvo == "pdf":
                            import fitz
                            self.event_pausa.wait()
                            doc = fitz.open()
                            page = doc.new_page()
                            with open(caminho_origem, "r", encoding="utf-8") as f:
                                texto = f.read()
                            page.insert_text((50, 50), texto)
                            doc.save(p_saida)
                            doc.close()
                            sucesso = True

                    # --- MOTOR PILLOW (Para Imagens) ---
                    elif fmt_alvo in ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'ico']:
                        from PIL import Image
                        self.event_pausa.wait()
                        with Image.open(caminho_origem) as img:
                            if fmt_alvo in ['jpg', 'jpeg'] and img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.save(p_saida)
                        sucesso = True

                    # Motor FFmpeg (Vídeo/Áudio)
                    else:
                        cmd = [self.ffmpeg_path, "-i", caminho_origem, "-preset", preset_alvo, "-y", p_saida]
                        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', creationflags=0x08000000)
                        
                        duracao_total = 1
                        for line in proc.stderr:
                            self.event_pausa.wait() # Suporte a Pausa
                            if self.cancelar_solicitado:
                                proc.terminate()
                                break
                            
                            if "Duration" in line:
                                match = re.search(r"Duration:\s(\d+):(\d+):(\d+).(\d+)", line)
                                if match:
                                    h, m, s, ms = map(int, match.groups())
                                    duracao_total = h*3600 + m*60 + s + ms/100
                            
                            if "time=" in line:
                                match = re.search(r"time=(\d+):(\d+):(\d+).(\d+)", line)
                                if match:
                                    h, m, s, ms = map(int, match.groups())
                                    atual = h*3600 + m*60 + s + ms/100
                                    porcentagem = (atual / duracao_total) * 100
                                    restante = max(0, duracao_total - atual)
                                    self.root.after(0, lambda p=porcentagem, n=nome_arquivo, r=restante: atualizar_status_live(p, n, r))
                        
                        proc.wait()
                        sucesso = (proc.returncode == 0) and not self.cancelar_solicitado

                except Exception as e:
                    print(f"Erro: {e}")
                    sucesso = False

                arquivos_concluidos += 1
                tag = "concluido" if sucesso else "erro"
                status_txt = "Concluído" if sucesso else ("Cancelado" if self.cancelar_solicitado else "Falha")
                ok_txt = "OK" if sucesso else "ERRO"
                self.root.after(0, lambda: self.tree.item(item_id, values=(nome_arquivo, tamanho, ok_txt, status_txt), tags=(tag,)))

        # Iniciar Threads
        for i, item_id in enumerate(self.tree.get_children()):
            t = threading.Thread(target=processar_item, args=(item_id, self.arquivos_data[i]), daemon=True)
            threads_em_andamento.append(t)
            t.start()

        for t in threads_em_andamento: t.join()
        self.root.after(0, self.finalizar_uai)

    def finalizar_uai(self):
        self.esta_convertendo = False
        self.btn_conv.config(text="INICIAR CONVERSÃO", state="normal")
        self.btn_cancelar.pack_forget()
        
        # Reativar UI
        self.btn_add.config(state="normal")
        self.btn_remover.config(state="normal")
        self.btn_limpar.config(state="normal")
        self.btn_seletor.config(state="normal")
        self.combo_paralelo.config(state="readonly")
        
        if self.cancelar_solicitado:
            self.status_label.config(text="⚠ Processamento cancelado.")
            messagebox.showwarning("Cancelado", "A operação foi interrompida.")
        else:
            self.status_label.config(text="✔ Processamento finalizado!")
            messagebox.showinfo("Sucesso", "Conversão finalizada!")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = Main(root)
    root.mainloop()