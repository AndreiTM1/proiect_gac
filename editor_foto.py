import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter
import cv2
import numpy as np

class EditorFotoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor Foto - Neactivat 25 Zile Ramase")
        self.root.geometry("1600x900")
        
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # ARHITECTURA NOUA DE IMAGINI
        self.imagine_absolut_originala = None 
        self.imagine_originala = None         
        self.imagine_baza = None              
        self.imagine_curenta = None           
        self.tk_imagine = None
        
        # Stive pentru Undo / Redo
        self.istoric_undo = []
        self.istoric_redo = []
        
        # Variabile desenare
        self.rect_id = None
        self.start_x = None
        self.start_y = None
        self.selectie_curenta = None
        self.afisaj_w = 1
        self.afisaj_h = 1

        # Variabile Pensula si Globale
        self.nume_filtru_brush = None
        self.brush_cursor = None
        self.dim_brush = tk.IntVar(value=30)
        self.imagine_baza_filtrata_brush = None
        self.is_brushing = False
        
        self.filtre_globale_active = [] 
        self.btn_filtre = {}            
        self.slider_timer = None        
        self.reset_allowed = False      
        
        self.creare_interfata()
        self.setari_scurtaturi()

    def setari_scurtaturi(self):
        self.root.bind("<Control-plus>", self.mareste_brush)
        self.root.bind("<Control-equal>", self.mareste_brush) 
        self.root.bind("<Control-minus>", self.micsoreaza_brush)
        self.root.bind("<Control-KP_Add>", self.mareste_brush)
        self.root.bind("<Control-KP_Subtract>", self.micsoreaza_brush)

        self.root.bind("<Control-Left>", lambda e: self.roteste_imagine(90))
        self.root.bind("<Control-Right>", lambda e: self.roteste_imagine(270))

        self.root.bind("<Control-s>", lambda e: self.salveaza_imagine()) 
        self.root.bind("<Control-o>", lambda e: self.deschide_imagine()) 

        self.root.bind("<Control-r>", lambda e: self.reseteaza_imagine()) 

        self.root.bind("<Control-w>", lambda e: self.deschide_wiki_scurtaturi()) 

        self.root.bind("<Control-b>", lambda e: self.mod_lucru.set("BRUSH"))
        self.root.bind("<Control-g>", lambda e: self.mod_lucru.set("GLOBAL"))
        self.root.bind("<Control-n>", lambda e: self.mod_lucru.set("SELECTIE"))
        
        # Scurtaturi pentru Undo si Redo
        self.root.bind("<Control-z>", lambda e: self.actiune_undo())
        self.root.bind("<Control-y>", lambda e: self.actiune_redo())

    def get_functii_filtre(self):
        return {
            "Grayscale": lambda img: img.convert("L"),
            "Negativare": self.logica_negativ,
            "Binarizare": lambda img: self.logica_binarizare(img, int(self.slider_prag.get())),
            "Chromatic Abr.": lambda img: self.logica_aberration(img, int(self.slider_aberration.get())),
            "Blur": lambda img: img.filter(ImageFilter.GaussianBlur(radius=self.slider_blur.get())),
            "Canny Edge": self.logica_canny,
            "Sare si Piper": self.logica_sare_piper
        }

    def creare_interfata(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame, padding="5", relief=tk.GROOVE)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.btn_deschide = ttk.Button(top_frame, text="Deschide Poza", underline = 10, command=self.deschide_imagine)
        self.btn_deschide.pack(side=tk.LEFT, padx=5)

        self.btn_salveaza = ttk.Button(top_frame, text="Salveaza Poza", underline = 0, command=self.salveaza_imagine, state=tk.DISABLED)
        self.btn_salveaza.pack(side=tk.LEFT, padx=5)
        
        # --- BUTOANE NOI UNDO SI REDO ---
        self.btn_undo = ttk.Button(top_frame, text="↩ Undo", command=self.actiune_undo, state=tk.DISABLED)
        self.btn_undo.pack(side=tk.LEFT, padx=(20, 5))

        self.btn_redo = ttk.Button(top_frame, text="↪ Redo", command=self.actiune_redo, state=tk.DISABLED)
        self.btn_redo.pack(side=tk.LEFT, padx=5)

        self.btn_reset = ttk.Button(top_frame, text="Resetare Imagine", underline = 0, command=self.reseteaza_imagine, state=tk.DISABLED)
        self.btn_reset.pack(side=tk.LEFT, padx=(20, 5))

        self.lbl_status = ttk.Label(top_frame, text="Nicio imagine incarcata", foreground="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        left_holder = ttk.Frame(main_frame, width=240)
        left_holder.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.left_canvas = tk.Canvas(left_holder, width=240, highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(left_holder, orient=tk.VERTICAL, command=self.left_canvas.yview)
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.left_canvas, width=240, padding="10", relief=tk.RIDGE)
        self.left_window_id = self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")
        
        self.left_frame.bind(
            "<Configure>",
            lambda e: (self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")), self._update_left_scrollbar_visibility())
        )
        
        self.left_canvas.bind("<Configure>", self._on_canvas_configure)
        self.root.after(0, self._update_left_scrollbar_visibility)

        self.root.bind_all("<MouseWheel>", self._on_left_mousewheel)
        self.root.bind_all("<Button-4>", self._on_left_mousewheel)
        self.root.bind_all("<Button-5>", self._on_left_mousewheel)

        ttk.Label(self.left_frame, text="Mod de Lucru", font=("Helvetica", 11, "bold")).pack(pady=(0, 5))
        self.mod_lucru = tk.StringVar(value="GLOBAL")
        
        ttk.Radiobutton(self.left_frame, text="Global", underline = 0, variable=self.mod_lucru, value="GLOBAL", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(self.left_frame, text="Selection", underline = 8, variable=self.mod_lucru, value="SELECTIE", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(self.left_frame, text="Brush",underline = 0, variable=self.mod_lucru, value="BRUSH", command=self.schimba_mod).pack(fill=tk.X)
        
        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(self.left_frame, text="Marime Pensula", font=("Helvetica", 9)).pack()
        self.slider_brush = ttk.Scale(self.left_frame, from_=5, to=150, variable=self.dim_brush, orient=tk.HORIZONTAL)
        self.slider_brush.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # SECTIUNEA TRANSFORMARE
        self.frame_transformare = ttk.Frame(self.left_frame)
        self.frame_transformare.pack(fill=tk.X, pady=0)
        
        ttk.Label(self.frame_transformare, text="Transformare", font=("Helvetica", 11, "bold")).pack(pady=(5, 5))

        btn_rot_frame = ttk.Frame(self.frame_transformare)
        btn_rot_frame.pack(fill=tk.X, pady=2)
        
        self.btn_rot_ccw = ttk.Button(btn_rot_frame, text="Rotire ↺", state=tk.DISABLED, command=lambda: self.roteste_imagine(90))
        self.btn_rot_ccw.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        self.btn_rot_cw = ttk.Button(btn_rot_frame, text="Rotire ↻", state=tk.DISABLED, command=lambda: self.roteste_imagine(270))
        self.btn_rot_cw.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        self.var_resize = tk.BooleanVar(value=False)
        self.chk_resize = ttk.Checkbutton(self.frame_transformare, text="Dimensiuni (Resize)", variable=self.var_resize, command=self.toggle_resize_ui, state=tk.DISABLED)
        self.chk_resize.pack(fill=tk.X, pady=5)

        self.frame_resize = ttk.Frame(self.frame_transformare)
        
        # Row 1: Setari manuale W si H
        frame_wh = ttk.Frame(self.frame_resize)
        frame_wh.pack(fill=tk.X, pady=2)
        
        lbl_w = ttk.Label(frame_wh, text="W:")
        lbl_w.pack(side=tk.LEFT, padx=2)
        self.entry_w = ttk.Entry(frame_wh, width=5)
        self.entry_w.pack(side=tk.LEFT, padx=2)

        lbl_h = ttk.Label(frame_wh, text="H:")
        lbl_h.pack(side=tk.LEFT, padx=2)
        self.entry_h = ttk.Entry(frame_wh, width=5)
        self.entry_h.pack(side=tk.LEFT, padx=2)

        self.btn_aplica_resize = ttk.Button(frame_wh, text="Aplica", command=self.aplica_resize)
        self.btn_aplica_resize.pack(side=tk.LEFT, padx=4)

        # Row 2: Slide pentru Scale
        self.lbl_scale = ttk.Label(self.frame_resize, text="Scale: 1.00x", font=("Helvetica", 9))
        self.lbl_scale.pack(anchor=tk.W, pady=(5, 0))
        
        self.slider_scale = ttk.Scale(self.frame_resize, from_=0.5, to=3.0, orient=tk.HORIZONTAL, command=self.on_scale_change)
        self.slider_scale.set(1.0)
        self.slider_scale.pack(fill=tk.X, pady=(0, 5))

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # SECTIUNEA FILTRE
        ttk.Label(self.left_frame, text="Setari Filtre", font=("Helvetica", 11, "bold")).pack(pady=(5, 5))

        ttk.Label(self.left_frame, text="Binarizare (Prag)", font=("Helvetica", 9)).pack()
        self.slider_prag = ttk.Scale(self.left_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_prag.set(128)
        self.slider_prag.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(self.left_frame, text="Aberration (Intensitate)", font=("Helvetica", 9)).pack()
        self.slider_aberration = ttk.Scale(self.left_frame, from_=0, to=30, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_aberration.set(10)
        self.slider_aberration.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.left_frame, text="Blur (Radius)", font=("Helvetica", 9)).pack()
        self.slider_blur = ttk.Scale(self.left_frame, from_=0, to=10, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_blur.set(2)
        self.slider_blur.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # BUTOANE FILTRE
        lista_filtre = ["Grayscale", "Negativare", "Binarizare", "Chromatic Abr.", "Blur", "Canny Edge", "Sare si Piper"]
        
        for nume in lista_filtre:
            btn = ttk.Button(self.left_frame, text=nume, state=tk.DISABLED, 
                             command=lambda n=nume: self.proceseaza_actiune_filtru(n))
            btn.pack(fill=tk.X, pady=2)
            self.btn_filtre[nume] = btn

        ttk.Frame(self.left_frame).pack(expand=True)

        self.btn_wiki = ttk.Button(self.left_frame, text="Wiki Scurtaturi", underline=0, command=self.deschide_wiki_scurtaturi)
        self.btn_wiki.pack(fill=tk.X, pady=(10, 0))

        # Zona Centrala
        display_frame = ttk.Frame(main_frame, relief=tk.SUNKEN)
        display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas_imagine = tk.Canvas(display_frame, bg="#2e2e2e", cursor="cross")
        self.canvas_imagine.pack(expand=True, fill=tk.BOTH)

        self.canvas_imagine.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas_imagine.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas_imagine.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas_imagine.bind("<Motion>", self.on_mouse_motion)
        self.canvas_imagine.bind("<Leave>", self.on_mouse_leave)
        
        self.canvas_imagine.bind("<ButtonPress-2>", self.start_pan)
        self.canvas_imagine.bind("<B2-Motion>", self.do_pan)
        self.canvas_imagine.bind("<ButtonPress-3>", self.start_pan)
        self.canvas_imagine.bind("<B3-Motion>", self.do_pan)

    def actualizeaza_layout_stanga(self):
        # Fortam interfata sa isi aplice geometria imediat
        self.left_frame.update_idletasks()
        
        req_height = self.left_frame.winfo_reqheight()
        canvas_height = self.left_canvas.winfo_height()
        
        # Mărim interiorul Canvasului dacă e nevoie de mai mult spațiu
        noua_inaltime = max(req_height, canvas_height)
        self.left_canvas.itemconfig(self.left_window_id, height=noua_inaltime)
        
        # Recalculăm scroll-ul
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        self._update_left_scrollbar_visibility()

    def _on_canvas_configure(self, event):
        self.left_canvas.itemconfig(self.left_window_id, width=event.width)
        req_height = self.left_frame.winfo_reqheight()
        noua_inaltime = max(req_height, event.height)
        self.left_canvas.itemconfig(self.left_window_id, height=noua_inaltime)
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        self._update_left_scrollbar_visibility()

    def _on_left_mousewheel(self, event):
        try:
            x = self.root.winfo_pointerx() - self.left_canvas.winfo_rootx()
            y = self.root.winfo_pointery() - self.left_canvas.winfo_rooty()
            if 0 <= x <= self.left_canvas.winfo_width() and 0 <= y <= self.left_canvas.winfo_height():
                if getattr(event, 'num', 0) == 4 or getattr(event, 'delta', 0) > 0:
                    self.left_canvas.yview_scroll(-1, "units")
                elif getattr(event, 'num', 0) == 5 or getattr(event, 'delta', 0) < 0:
                    self.left_canvas.yview_scroll(1, "units")
        except tk.TclError:
            pass 

    def _update_left_scrollbar_visibility(self):
        bbox = self.left_canvas.bbox("all")
        view_height = self.left_canvas.winfo_height()
        if view_height <= 1:
            self.root.after(50, self._update_left_scrollbar_visibility)
            return
        if not bbox:
            if self.left_scrollbar.winfo_ismapped():
                self.left_scrollbar.pack_forget()
            return

        content_height = bbox[3] - bbox[1]
        if content_height > view_height:
            if not self.left_scrollbar.winfo_ismapped():
                self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            if self.left_scrollbar.winfo_ismapped():
                self.left_scrollbar.pack_forget()

    # --- LOGICA UNDO / REDO ---
    def salveaza_stare_undo(self):
        if self.imagine_baza:
            self.istoric_undo.append(self.imagine_baza.copy())
            if len(self.istoric_undo) > 15:
                self.istoric_undo.pop(0)
            self.istoric_redo.clear() 
            self.reset_allowed = True
            self.actualizeaza_butoane_undo_redo()

    def actiune_undo(self):
        if self.mod_lucru.get() == "GLOBAL" or not self.istoric_undo: return
        
        self.istoric_redo.append(self.imagine_baza.copy())
        self.imagine_baza = self.istoric_undo.pop()
        
        self.recalculeaza_imagine_globala()
        self.actualizeaza_butoane_undo_redo()

    def actiune_redo(self):
        if self.mod_lucru.get() == "GLOBAL" or not self.istoric_redo: return
        
        self.istoric_undo.append(self.imagine_baza.copy())
        self.imagine_baza = self.istoric_redo.pop()
        
        self.recalculeaza_imagine_globala()
        self.actualizeaza_butoane_undo_redo()

    def actualizeaza_butoane_undo_redo(self):
        if self.mod_lucru.get() == "GLOBAL" or not self.imagine_baza:
            self.btn_undo.config(state=tk.DISABLED)
            self.btn_redo.config(state=tk.DISABLED)
        else:
            self.btn_undo.config(state=tk.NORMAL if self.istoric_undo else tk.DISABLED)
            self.btn_redo.config(state=tk.NORMAL if self.istoric_redo else tk.DISABLED)

    # --- ACTIUNI ROTIRE SI RESIZE (SMART OBJECT) ---
    def roteste_imagine(self, unghi):
        if not self.imagine_baza: return
        self.reset_allowed = True
        if unghi == 90:
            self.imagine_baza = self.imagine_baza.transpose(Image.ROTATE_90)
            self.imagine_originala = self.imagine_originala.transpose(Image.ROTATE_90)
        elif unghi == 270:
            self.imagine_baza = self.imagine_baza.transpose(Image.ROTATE_270)
            self.imagine_originala = self.imagine_originala.transpose(Image.ROTATE_270)
            
        self.sterge_selectia_vizuala()
        self.recalculeaza_imagine_globala()
        
        if self.var_resize.get() and self.imagine_originala:
            scale_curent = self.imagine_baza.width / self.imagine_originala.width
            self.slider_scale.set(scale_curent)
            self.lbl_scale.config(text=f"Scale: {scale_curent:.2f}x")
            self.entry_w.delete(0, tk.END)
            self.entry_w.insert(0, str(self.imagine_baza.width))
            self.entry_h.delete(0, tk.END)
            self.entry_h.insert(0, str(self.imagine_baza.height))

    def on_scale_change(self, val):
        if not self.imagine_originala: return
        scale = float(val)
        self.lbl_scale.config(text=f"Scale: {scale:.2f}x")
        
        new_w = int(self.imagine_originala.width * scale)
        new_h = int(self.imagine_originala.height * scale)
        
        self.entry_w.delete(0, tk.END)
        self.entry_w.insert(0, str(new_w))
        self.entry_h.delete(0, tk.END)
        self.entry_h.insert(0, str(new_h))

    def toggle_resize_ui(self):
        if self.var_resize.get():
            self.frame_resize.pack(fill=tk.X, pady=2)
            if self.imagine_baza and self.imagine_originala:
                scale_curent = self.imagine_baza.width / self.imagine_originala.width
                self.slider_scale.set(scale_curent)
                self.lbl_scale.config(text=f"Scale: {scale_curent:.2f}x")
                self.entry_w.delete(0, tk.END)
                self.entry_w.insert(0, str(self.imagine_baza.width))
                self.entry_h.delete(0, tk.END)
                self.entry_h.insert(0, str(self.imagine_baza.height))
        else:
            self.frame_resize.pack_forget()
            
        # Apelam functia de actualizare layout dupa ce am afisat/ascuns panoul
        self.actualizeaza_layout_stanga()

    def aplica_resize(self):
        if not self.imagine_originala: return
        try:
            new_w = int(self.entry_w.get())
            new_h = int(self.entry_h.get())
            if new_w > 0 and new_h > 0:
                try:
                    resample_filter = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_filter = Image.LANCZOS
                    
                self.imagine_baza = self.imagine_originala.resize((new_w, new_h), resample_filter)
                self.reset_allowed = True
                
                scale_curent = new_w / self.imagine_originala.width
                scale_curent = max(0.5, min(3.0, scale_curent))
                self.slider_scale.set(scale_curent)
                self.lbl_scale.config(text=f"Scale: {scale_curent:.2f}x")
                
                self.sterge_selectia_vizuala()
                self.recalculeaza_imagine_globala()
        except ValueError:
            messagebox.showerror("Eroare", "Dimensiunile trebuie sa fie numere intregi.")

    def on_slider_change(self, val):
        if self.slider_timer:
            self.root.after_cancel(self.slider_timer)
        self.slider_timer = self.root.after(100, self.executa_recalculare_slider)

    def executa_recalculare_slider(self):
        if self.mod_lucru.get() == "GLOBAL" and self.filtre_globale_active:
            self.recalculeaza_imagine_globala()

    def mareste_brush(self, event=None):
        self.dim_brush.set(min(150, self.dim_brush.get() + 5))
        if event and hasattr(event, 'x'): self.actualizeaza_cerc_brush(event.x, event.y)

    def micsoreaza_brush(self, event=None):
        self.dim_brush.set(max(5, self.dim_brush.get() - 5))
        if event and hasattr(event, 'x'): self.actualizeaza_cerc_brush(event.x, event.y)

    def schimba_mod(self):
        self.sterge_selectia_vizuala()
        self.nume_filtru_brush = None
        self.imagine_baza_filtrata_brush = None
        self.is_brushing = False
        
        if self.brush_cursor:
            self.canvas_imagine.delete(self.brush_cursor)
            self.brush_cursor = None

        if not self.imagine_baza: return

        mod = self.mod_lucru.get()
        if mod == "BRUSH":
            self.lbl_status.config(text="Mod Pensula: Alege un filtru pentru a incarca pensula.")
            self.activeaza_filtre()
        elif mod == "SELECTIE":
            self.lbl_status.config(text="Mod Selectie: Traseaza un chenar pe poza.")
            self.dezactiveaza_filtre()
        else:
            self.lbl_status.config(text="Mod Global: Activeaza sau dezactiveaza straturile de filtre.")
            self.activeaza_filtre()
            
        self.actualizeaza_butoane_undo_redo()

    def dezactiveaza_filtre(self):
        for btn in self.btn_filtre.values(): btn.config(state=tk.DISABLED)

    def activeaza_filtre(self):
        if self.imagine_baza:
            for btn in self.btn_filtre.values(): btn.config(state=tk.NORMAL)

    def deschide_imagine(self):
        cale_fisier = filedialog.askopenfilename(
            title="Alege o imagine",
            filetypes=[("Imagini suportate", "*.png *.jpg *.jpeg *.JPG *.JPEG")]
        )
        if cale_fisier:
            try:
                self.imagine_absolut_originala = Image.open(cale_fisier)
                self.imagine_originala = self.imagine_absolut_originala.copy()
                self.imagine_baza = self.imagine_originala.copy()
                self.filtre_globale_active.clear()
                
                self.istoric_undo.clear()
                self.istoric_redo.clear()
                self.reset_allowed = True
                
                for nume, btn in self.btn_filtre.items():
                    btn.config(text=nume)
                
                self.btn_salveaza.config(state=tk.NORMAL)
                self.btn_reset.config(state=tk.NORMAL)
                
                self.btn_rot_ccw.config(state=tk.NORMAL)
                self.btn_rot_cw.config(state=tk.NORMAL)
                self.chk_resize.config(state=tk.NORMAL)

                self.schimba_mod() 
                self.recalculeaza_imagine_globala()
                self.actualizeaza_butoane_undo_redo()
                
                if self.var_resize.get() and self.imagine_originala:
                    self.slider_scale.set(1.0)
                    self.lbl_scale.config(text="Scale: 1.00x")
                    self.entry_w.delete(0, tk.END)
                    self.entry_w.insert(0, str(self.imagine_originala.width))
                    self.entry_h.delete(0, tk.END)
                    self.entry_h.insert(0, str(self.imagine_originala.height))
                
                nume_fisier = cale_fisier.split('/')[-1]
                self.lbl_status.config(text=f"Fisier deschis: {nume_fisier}")
            except Exception as e:
                messagebox.showerror("Eroare", f"Nu s-a putut deschide imaginea:\n{e}")

    def salveaza_imagine(self):
        if self.imagine_curenta:
            cale_salvare = filedialog.asksaveasfilename(
                title="Salveaza imaginea editata",
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.JPG *.jpeg *.JPEG")]
            )
            if cale_salvare:
                try:
                    if cale_salvare.lower().endswith(('.jpg', '.jpeg')) and self.imagine_curenta.mode != "RGB":
                        imagine_salvare = self.imagine_curenta.convert("RGB")
                    else:
                        imagine_salvare = self.imagine_curenta
                    imagine_salvare.save(cale_salvare)
                    messagebox.showinfo("Succes", "Imaginea a fost salvata cu succes!")
                except Exception as e:
                    messagebox.showerror("Eroare", f"Nu s-a putut salva imaginea:\n{e}")

    def reseteaza_imagine(self):
        if not self.reset_allowed:
            return
        if self.imagine_absolut_originala:
            self.salveaza_stare_undo()
            self.imagine_originala = self.imagine_absolut_originala.copy()
            self.imagine_baza = self.imagine_originala.copy()
            self.reset_allowed = False
            
            self.filtre_globale_active.clear()
            self.imagine_baza_filtrata_brush = None
            
            for nume, btn in self.btn_filtre.items():
                btn.config(text=nume)
                
            self.sterge_selectia_vizuala()
            self.recalculeaza_imagine_globala()
            self.actualizeaza_butoane_undo_redo()
            
            if self.var_resize.get() and self.imagine_originala:
                self.slider_scale.set(1.0)
                self.lbl_scale.config(text="Scale: 1.00x")
                self.entry_w.delete(0, tk.END)
                self.entry_w.insert(0, str(self.imagine_originala.width))
                self.entry_h.delete(0, tk.END)
                self.entry_h.insert(0, str(self.imagine_originala.height))

    def recalculeaza_imagine_globala(self):
        if not self.imagine_baza: return
        
        img_temp = self.imagine_baza.copy()
        functii = self.get_functii_filtre()
        
        for nume_filtru in self.filtre_globale_active:
            img_temp = functii[nume_filtru](img_temp)
            
        self.imagine_curenta = img_temp
        self.actualizeaza_afisaj()

    def proceseaza_actiune_filtru(self, nume_filtru):
        if not self.imagine_baza: return
        mod = self.mod_lucru.get()

        if mod == "GLOBAL":
            if nume_filtru in self.filtre_globale_active:
                self.filtre_globale_active.remove(nume_filtru)
                self.btn_filtre[nume_filtru].config(text=nume_filtru)
            else:
                self.filtre_globale_active.append(nume_filtru)
                self.btn_filtre[nume_filtru].config(text=f"* {nume_filtru}")
            
            self.reset_allowed = True
            self.recalculeaza_imagine_globala()
            
        elif mod == "SELECTIE" and self.selectie_curenta:
            raport_w = self.imagine_baza.width / self.afisaj_w
            raport_h = self.imagine_baza.height / self.afisaj_h
            
            x1, y1, x2, y2 = self.selectie_curenta
            x1, y1 = max(0, int(x1 * raport_w)), max(0, int(y1 * raport_h))
            x2, y2 = min(self.imagine_baza.width, int(x2 * raport_w)), min(self.imagine_baza.height, int(y2 * raport_h))
            
            roi = self.imagine_baza.crop((x1, y1, x2, y2))
            functie_activa = self.get_functii_filtre()[nume_filtru]
            roi_procesat = functie_activa(roi)
            
            if self.imagine_baza.mode != roi_procesat.mode:
                roi_procesat = roi_procesat.convert(self.imagine_baza.mode)
                
            self.salveaza_stare_undo()
            
            self.imagine_baza.paste(roi_procesat, (x1, y1))
            self.sterge_selectia_vizuala()
            self.recalculeaza_imagine_globala()
            
        elif mod == "BRUSH":
            self.nume_filtru_brush = nume_filtru
            self.lbl_status.config(text=f"Pensula incarcata cu: {nume_filtru}")

    def actualizeaza_afisaj(self):
        if self.imagine_curenta:
            img_afisare = self.imagine_curenta.copy()
            img_afisare.thumbnail((800, 650))
            
            self.afisaj_w = img_afisare.width
            self.afisaj_h = img_afisare.height
            
            self.tk_imagine = ImageTk.PhotoImage(img_afisare)
            
            self.canvas_imagine.delete("img_tag")
            self.canvas_imagine.config(scrollregion=(0, 0, self.afisaj_w, self.afisaj_h))
            self.canvas_imagine.create_image(0, 0, anchor=tk.NW, image=self.tk_imagine, tags="img_tag")
            self.canvas_imagine.tag_lower("img_tag")
            
            if self.brush_cursor:
                self.canvas_imagine.tag_raise(self.brush_cursor)

    def start_pan(self, event):
        self.canvas_imagine.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas_imagine.scan_dragto(event.x, event.y, gain=1)

    def on_mouse_press(self, event):
        if not self.imagine_baza: return
        mod = self.mod_lucru.get()
        cx = self.canvas_imagine.canvasx(event.x)
        cy = self.canvas_imagine.canvasy(event.y)

        if mod == "SELECTIE":
            self.start_x = max(0, min(cx, self.afisaj_w))
            self.start_y = max(0, min(cy, self.afisaj_h))
            self.sterge_selectia_vizuala()
            self.dezactiveaza_filtre()
            self.rect_id = self.canvas_imagine.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2, dash=(4, 4)
            )
        elif mod == "BRUSH" and self.nume_filtru_brush:
            self.salveaza_stare_undo()
            
            functie = self.get_functii_filtre()[self.nume_filtru_brush]
            self.imagine_baza_filtrata_brush = functie(self.imagine_baza)
            if self.imagine_baza.mode != self.imagine_baza_filtrata_brush.mode:
                self.imagine_baza_filtrata_brush = self.imagine_baza_filtrata_brush.convert(self.imagine_baza.mode)
            
            self.is_brushing = True
            self.aplica_brush(cx, cy)

    def on_mouse_drag(self, event):
        if not self.imagine_baza: return
        mod = self.mod_lucru.get()
        cx = self.canvas_imagine.canvasx(event.x)
        cy = self.canvas_imagine.canvasy(event.y)
        
        cur_x = max(0, min(cx, self.afisaj_w))
        cur_y = max(0, min(cy, self.afisaj_h))

        if mod == "SELECTIE" and self.rect_id:
            self.canvas_imagine.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
        elif mod == "BRUSH" and self.is_brushing:
            self.actualizeaza_cerc_brush(event.x, event.y)
            self.aplica_brush(cur_x, cur_y)

    def on_mouse_release(self, event):
        if not self.imagine_baza: return
        mod = self.mod_lucru.get()
        cx = self.canvas_imagine.canvasx(event.x)
        cy = self.canvas_imagine.canvasy(event.y)

        if mod == "SELECTIE" and self.rect_id:
            cur_x = max(0, min(cx, self.afisaj_w))
            cur_y = max(0, min(cy, self.afisaj_h))
            if abs(cur_x - self.start_x) > 5 and abs(cur_y - self.start_y) > 5:
                self.selectie_curenta = (min(self.start_x, cur_x), min(self.start_y, cur_y),
                                         max(self.start_x, cur_x), max(self.start_y, cur_y))
                self.activeaza_filtre() 
            else:
                self.sterge_selectia_vizuala()
        elif mod == "BRUSH":
            self.is_brushing = False
            self.imagine_baza_filtrata_brush = None

    def on_mouse_motion(self, event):
        if self.mod_lucru.get() == "BRUSH":
            self.actualizeaza_cerc_brush(event.x, event.y)

    def on_mouse_leave(self, event):
        if self.brush_cursor:
            self.canvas_imagine.delete(self.brush_cursor)
            self.brush_cursor = None

    def actualizeaza_cerc_brush(self, window_x, window_y):
        if self.brush_cursor: self.canvas_imagine.delete(self.brush_cursor)
        cx = self.canvas_imagine.canvasx(window_x)
        cy = self.canvas_imagine.canvasy(window_y)
        r = self.dim_brush.get()
        
        if 0 <= cx <= self.afisaj_w and 0 <= cy <= self.afisaj_h:
            self.brush_cursor = self.canvas_imagine.create_oval(
                cx - r, cy - r, cx + r, cy + r, outline="white", dash=(2, 2)
            )

    def sterge_selectia_vizuala(self):
        if self.rect_id:
            self.canvas_imagine.delete(self.rect_id)
            self.rect_id = None
        self.selectie_curenta = None

    def aplica_brush(self, cx, cy):
        if not self.imagine_baza_filtrata_brush: return

        raport_w = self.imagine_baza.width / self.afisaj_w
        raport_h = self.imagine_baza.height / self.afisaj_h
        
        orig_x, orig_y = int(cx * raport_w), int(cy * raport_h)
        orig_r = int(self.dim_brush.get() * max(raport_w, raport_h)) 
        
        left, upper = max(0, orig_x - orig_r), max(0, orig_y - orig_r)
        right, lower = min(self.imagine_baza.width, orig_x + orig_r), min(self.imagine_baza.height, orig_y + orig_r)
        
        if left >= right or upper >= lower: return

        roi_procesat = self.imagine_baza_filtrata_brush.crop((left, upper, right, lower))
        
        mask = Image.new("L", (right - left, lower - upper), 0)
        draw = ImageDraw.Draw(mask)
        c_x, c_y = orig_x - left, orig_y - upper
        draw.ellipse((c_x - orig_r, c_y - orig_r, c_x + orig_r, c_y + orig_r), fill=255)
        
        self.imagine_baza.paste(roi_procesat, (left, upper), mask)
        self.recalculeaza_imagine_globala()


    def deschide_wiki_scurtaturi(self):
        fereastra_wiki = tk.Toplevel(self.root)
        fereastra_wiki.title("Wiki Scurtături")
        fereastra_wiki.geometry("400x350")
        
        fereastra_wiki.transient(self.root)
        
        text_wiki = tk.Text(fereastra_wiki, wrap=tk.WORD, font=("Helvetica", 10), padx=15, pady=15, bg="#f9f9f9")
        text_wiki.pack(expand=True, fill=tk.BOTH)
        
        continut = """ 
        Scurtături de la tastatură:
        - Ctrl + O: Deschide o imagine
        - Ctrl + S: Salvează imaginea curentă
        - Ctrl + Z: Undo
        - Ctrl + Y: Redo
        - Ctrl + R: Reset imagine
        - Ctrl + +: Mărește dimensiunea pensulei
        - Ctrl + -: Micșorează dimensiunea pensulei
        - Ctrl + G: Mod Global
        - Ctrl + N: Mod Selecție
        - Ctrl + B: Mod Pensulă
        - Ctrl + Left: Rotire ↺
        - Ctrl + Right: Rotire ↻"""

        text_wiki.insert(tk.END, continut.strip())
        text_wiki.config(state=tk.DISABLED)

    # --- FUNCTII FILTRE MATEMATICE INDIVIDUALE ---

    def logica_negativ(self, img):
        if img.mode == "RGBA":
            r, g, b, a = img.split()
            img_rgb = Image.merge("RGB", (r, g, b))
            img_inversata = ImageOps.invert(img_rgb)
            r2, g2, b2 = img_inversata.split()
            return Image.merge("RGBA", (r2, g2, b2, a))
        else:
            if img.mode == '1': img = img.convert("L")
            return ImageOps.invert(img)

    def logica_binarizare(self, img, prag):
        return img.convert("L").point(lambda p: 255 if p > prag else 0)

    def logica_aberration(self, img, deplasare):
        if deplasare == 0: return img
        img_rgb = img.convert("RGB")
        r, g, b = img_rgb.split()
        w, h = img_rgb.size
        r_shift = r.transform((w, h), Image.AFFINE, (1, 0, deplasare, 0, 1, 0))
        b_shift = b.transform((w, h), Image.AFFINE, (1, 0, -deplasare, 0, 1, 0))
        return Image.merge("RGB", (r_shift, g, b_shift))

    def logica_canny(self, img):
        img_array = np.array(img.convert("RGB"))
        img_gri_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        contururi = cv2.Canny(img_gri_cv2, 100, 200)
        return Image.fromarray(contururi)

    def logica_sare_piper(self, img):
        prob = 0.05
        img_array = np.array(img.convert("RGB"))
        noise = np.random.rand(img_array.shape[0], img_array.shape[1])
        
        img_array[noise < (prob / 2)] = [255, 255, 255]
        img_array[noise > (1 - prob / 2)] = [0, 0, 0]
        
        if img.mode != "RGB":
            return Image.fromarray(img_array).convert(img.mode)
        return Image.fromarray(img_array)

if __name__ == "__main__":
    root = tk.Tk()
    app = EditorFotoApp(root)
    root.mainloop()