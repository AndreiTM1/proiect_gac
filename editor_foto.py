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
        
        # Starea temei
        self.is_dark_mode = False
        
        # Seteaza fundalul ferestrei principale pentru Light Mode
        self.bg_main = "#f0f0f0"
        self.bg_panel = "#e0e0e0"
        self.fg_text = "#000000"
        self.root.configure(bg=self.bg_main)
        
        self.configurare_tema()

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

    def configurare_tema(self):
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # Culori variabile in functie de tema activa
        if self.is_dark_mode:
            accent_blue = "#4B6EAF"
            accent_blue_hover = "#5C7CB8"
            accent_green = "#497A42"
            accent_green_hover = "#558F4D"
            accent_red = "#9E4545"
            accent_red_hover = "#B34E4E"
            accent_primary = "#7E57C2" 
            accent_primary_hover = "#9575CD"
            btn_normal = "#4B4D4D"
            btn_active = "#5A5C5C"
            btn_disabled = "#323232"
            fg_disabled = "#707070"
            entry_bg = self.bg_main
            entry_border = "#555"
            fg_action_text = self.fg_text
            select_color = self.bg_main
            trough_color = self.bg_main
        else:
            accent_blue = "#0078D7"
            accent_blue_hover = "#005A9E"
            accent_green = "#107C10"
            accent_green_hover = "#0B5A0B"
            accent_red = "#D13438"
            accent_red_hover = "#A4262C"
            accent_primary = "#673AB7" 
            accent_primary_hover = "#512DA8"
            btn_normal = "#e1e1e1"
            btn_active = "#d1d1d1"
            btn_disabled = "#f0f0f0"
            fg_disabled = "#a0a0a0"
            entry_bg = "#FFFFFF"
            entry_border = "#8A8886"
            fg_action_text = "#FFFFFF"
            select_color = "#FFFFFF"
            trough_color = "#c8c8c8"

        # Configurari globale pentru containere si text
        self.style.configure(".", background=self.bg_panel, foreground=self.fg_text)
        self.style.configure("TFrame", background=self.bg_panel)
        self.style.configure("Main.TFrame", background=self.bg_main)
        self.style.configure("TLabel", background=self.bg_panel, foreground=self.fg_text)
        
        self.style.configure("TRadiobutton", background=self.bg_panel, foreground=self.fg_text, selectcolor=select_color)
        self.style.map("TRadiobutton", 
            background=[("active", self.bg_panel)], 
            foreground=[("active", self.fg_text)]
        )
        
        self.style.configure("TCheckbutton", background=self.bg_panel, foreground=self.fg_text, selectcolor=select_color)
        self.style.map("TCheckbutton", 
            background=[("active", self.bg_panel)], 
            foreground=[("active", self.fg_text)]
        )

        self.style.configure("Horizontal.TScale", background=self.bg_panel, troughcolor=trough_color)
        self.style.configure("TSeparator", background=trough_color)
        
        self.style.configure("TEntry", fieldbackground=entry_bg, foreground=self.fg_text, bordercolor=entry_border, insertcolor=self.fg_text)

        # Configurarea butonului standard
        self.style.configure("TButton", background=btn_normal, foreground=self.fg_text, borderwidth=1, focuscolor=self.bg_main)
        self.style.map("TButton", 
            background=[("active", btn_active), ("disabled", btn_disabled)], 
            foreground=[("active", self.fg_text), ("disabled", fg_disabled)]
        )

        # Butoane Actiuni principale
        self.style.configure("Action.TButton", background=accent_blue, foreground=fg_action_text, font=("Helvetica", 9, "bold"))
        self.style.map("Action.TButton", 
            background=[("active", accent_blue_hover), ("disabled", btn_disabled)],
            foreground=[("active", fg_action_text), ("disabled", fg_disabled)]
        )

        # Butoane Salvare/Succes
        self.style.configure("Success.TButton", background=accent_green, foreground=fg_action_text, font=("Helvetica", 9, "bold"))
        self.style.map("Success.TButton", 
            background=[("active", accent_green_hover), ("disabled", btn_disabled)],
            foreground=[("active", fg_action_text), ("disabled", fg_disabled)]
        )

        # Butoane Reset/Stergere
        self.style.configure("Danger.TButton", background=accent_red, foreground=fg_action_text, font=("Helvetica", 9, "bold"))
        self.style.map("Danger.TButton", 
            background=[("active", accent_red_hover), ("disabled", btn_disabled)],
            foreground=[("active", fg_action_text), ("disabled", fg_disabled)]
        )

        # Butoane Secundare/Primary (Undo/Redo - Mov)
        self.style.configure("Primary.TButton", background=accent_primary, foreground=fg_action_text, font=("Helvetica", 9, "bold"))
        self.style.map("Primary.TButton", 
            background=[("active", accent_primary_hover), ("disabled", btn_disabled)],
            foreground=[("active", fg_action_text), ("disabled", fg_disabled)]
        )

    def schimba_tema(self):
        self.is_dark_mode = not self.is_dark_mode
        
        if not self.is_dark_mode:
            self.bg_main = "#f0f0f0"
            self.bg_panel = "#e0e0e0"
            self.fg_text = "#000000"
            self.btn_tema.config(text="Dark Mode")
            self.canvas_imagine.configure(bg="#2e2e2e") # In tema veche, canvas-ul cu imaginea era inchis la culoare
            self.lbl_status.configure(foreground="#555555")
        else:
            self.bg_main = "#2b2b2b"
            self.bg_panel = "#3c3f41"
            self.fg_text = "#d3d3d3"
            self.btn_tema.config(text="Light Mode")
            self.canvas_imagine.configure(bg=self.bg_main)
            self.lbl_status.configure(foreground="#a0a0a0")

        # Actualizam interfata in timp real
        self.root.configure(bg=self.bg_main)
        self.left_canvas.configure(bg=self.bg_panel)
        self.configurare_tema()

    def setari_scurtaturi(self):
        self.root.bind("<Control-equal>", self.mareste_brush) 
        self.root.bind("<Control-plus>", self.mareste_brush)
        self.root.bind("<Control-minus>", self.micsoreaza_brush)

        self.root.bind("<Control-Key-KP_Add>", self.mareste_brush)
        self.root.bind("<Control-Key-KP_Subtract>", self.micsoreaza_brush)

        self.root.bind("<Control-Up>", lambda e: self.ajusteaza_aberration(1))
        self.root.bind("<Control-Down>", lambda e: self.ajusteaza_aberration(-1))

        self.root.bind("<Control-Key-KP_Up>", lambda e: self.ajusteaza_blur(1))
        self.root.bind("<Control-Key-KP_Down>", lambda e: self.ajusteaza_blur(-1))

        self.root.bind("<Control-Key-KP_Right>", lambda e: self.ajusteaza_binarizare(1))
        self.root.bind("<Control-Key-KP_Left>", lambda e: self.ajusteaza_binarizare(-1))

        self.root.bind("<Control-Left>", lambda e: self.roteste_imagine(90))
        self.root.bind("<Control-Right>", lambda e: self.roteste_imagine(270)) 

        self.root.bind("<Control-w>", lambda e: self.deschide_wiki_scurtaturi()) 

        self.root.bind("<Control-b>", lambda e: self.mod_lucru.set("BRUSH"))
        self.root.bind("<Control-g>", lambda e: self.mod_lucru.set("GLOBAL"))
        self.root.bind("<Control-n>", lambda e: self.mod_lucru.set("SELECTIE"))

        self.root.bind("<Control-Key-1>", lambda e: self.proceseaza_actiune_filtru("Grayscale"))
        self.root.bind("<Control-Key-2>", lambda e: self.proceseaza_actiune_filtru("Negativare"))
        self.root.bind("<Control-Key-3>", lambda e: self.proceseaza_actiune_filtru("Binarizare"))
        self.root.bind("<Control-Key-4>", lambda e: self.proceseaza_actiune_filtru("Chromatic Abr."))
        self.root.bind("<Control-Key-5>", lambda e: self.proceseaza_actiune_filtru("Blur"))
        self.root.bind("<Control-Key-6>", lambda e: self.proceseaza_actiune_filtru("Canny Edge"))
        self.root.bind("<Control-Key-7>", lambda e: self.proceseaza_actiune_filtru("Sare si Piper"))

        self.root.bind("<Control-Key-KP_1>", lambda e: self.proceseaza_actiune_filtru("Grayscale"))
        self.root.bind("<Control-Key-KP_2>", lambda e: self.proceseaza_actiune_filtru("Negativare"))
        self.root.bind("<Control-Key-KP_3>", lambda e: self.proceseaza_actiune_filtru("Binarizare"))
        self.root.bind("<Control-Key-KP_4>", lambda e: self.proceseaza_actiune_filtru("Chromatic Abr."))
        self.root.bind("<Control-Key-KP_5>", lambda e: self.proceseaza_actiune_filtru("Blur"))
        self.root.bind("<Control-Key-KP_6>", lambda e: self.proceseaza_actiune_filtru("Canny Edge"))
        self.root.bind("<Control-Key-KP_7>", lambda e: self.proceseaza_actiune_filtru("Sare si Piper"))

        self.root.bind("<Control-o>", lambda e: self.deschide_imagine()) 
        self.root.bind("<Control-s>", lambda e: self.salveaza_imagine()) 
        self.root.bind("<Control-r>", lambda e: self.reseteaza_imagine())
        self.root.bind("<Control-z>", lambda e: self.actiune_undo())
        self.root.bind("<Control-y>", lambda e: self.actiune_redo())
        self.root.bind("<Control-h>", lambda e: self.afiseaza_histograma())

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
        main_frame = ttk.Frame(self.root, padding="10", style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame, padding="5", relief=tk.GROOVE)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.btn_deschide = ttk.Button(top_frame, text="Deschide Poza", underline=10, style="Action.TButton", command=self.deschide_imagine)
        self.btn_deschide.pack(side=tk.LEFT, padx=5)

        self.btn_salveaza = ttk.Button(top_frame, text="Salveaza Poza", underline=0, style="Success.TButton", command=self.salveaza_imagine, state=tk.DISABLED)
        self.btn_salveaza.pack(side=tk.LEFT, padx=5)
        
        self.btn_undo = ttk.Button(top_frame, text="Undo", style="Primary.TButton", command=self.actiune_undo, state=tk.DISABLED)
        self.btn_undo.pack(side=tk.LEFT, padx=(20, 5))

        self.btn_redo = ttk.Button(top_frame, text="Redo", style="Primary.TButton", command=self.actiune_redo, state=tk.DISABLED)
        self.btn_redo.pack(side=tk.LEFT, padx=5)

        self.btn_reset = ttk.Button(top_frame, text="Resetare Imagine", underline=0, style="Danger.TButton", command=self.reseteaza_imagine, state=tk.DISABLED)
        self.btn_reset.pack(side=tk.LEFT, padx=(20, 5))

        self.btn_histograma = ttk.Button(top_frame, text="Histograma", underline=0, style="Action.TButton", command=self.afiseaza_histograma, state=tk.DISABLED)
        self.btn_histograma.pack(side=tk.LEFT, padx=5)

        # Corectura 1: Textul butonului adaptat dinamic la pornire
        text_tema = "Light Mode" if self.is_dark_mode else "Dark Mode"
        self.btn_tema = ttk.Button(top_frame, text=text_tema, command=self.schimba_tema)
        self.btn_tema.pack(side=tk.RIGHT, padx=5)

        # Corectura 2: Culoarea statusului adaptată
        culoare_status = "#a0a0a0" if self.is_dark_mode else "#555555"
        self.lbl_status = ttk.Label(top_frame, text="Nicio imagine incarcata", foreground=culoare_status)
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        left_holder = ttk.Frame(main_frame, width=240, style="Main.TFrame")
        left_holder.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.left_canvas = tk.Canvas(left_holder, width=240, highlightthickness=0, bg=self.bg_panel)
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
        
        ttk.Radiobutton(self.left_frame, text="Global", underline=0, variable=self.mod_lucru, value="GLOBAL", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(self.left_frame, text="Selection", underline=8, variable=self.mod_lucru, value="SELECTIE", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(self.left_frame, text="Brush", underline=0, variable=self.mod_lucru, value="BRUSH", command=self.schimba_mod).pack(fill=tk.X)
        
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
        
        self.btn_rot_ccw = ttk.Button(btn_rot_frame, text="Rotire ⟲", state=tk.DISABLED, command=lambda: self.roteste_imagine(90))
        self.btn_rot_ccw.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        self.btn_rot_cw = ttk.Button(btn_rot_frame, text="Rotire ⟳", state=tk.DISABLED, command=lambda: self.roteste_imagine(270))
        self.btn_rot_cw.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        self.var_resize = tk.BooleanVar(value=False)
        self.chk_resize = ttk.Checkbutton(self.frame_transformare, text="Resize", variable=self.var_resize, command=self.toggle_resize_ui, state=tk.DISABLED)
        self.chk_resize.pack(fill=tk.X, pady=5)

        self.frame_resize = ttk.Frame(self.frame_transformare)
        
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

        self.btn_aplica_resize = ttk.Button(frame_wh, text="Aplica", style="Action.TButton", command=self.aplica_resize)
        self.btn_aplica_resize.pack(side=tk.LEFT, padx=4)

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

        # Corectura 3: Culoarea panoului de desenat stabilita corect la pornire
        culoare_canvas = self.bg_main if self.is_dark_mode else "#2e2e2e"
        self.canvas_imagine = tk.Canvas(display_frame, bg=culoare_canvas, cursor="cross", highlightthickness=0)
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
        self.left_frame.update_idletasks()
        req_height = self.left_frame.winfo_reqheight()
        canvas_height = self.left_canvas.winfo_height()
        noua_inaltime = max(req_height, canvas_height)
        self.left_canvas.itemconfig(self.left_window_id, height=noua_inaltime)
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

    def ajusteaza_aberration(self, valoare_schimbare):
        noua_valoare = self.slider_aberration.get() + valoare_schimbare
        noua_valoare = max(0, min(30, noua_valoare))
        self.slider_aberration.set(noua_valoare)
        self.executa_recalculare_slider()

    def ajusteaza_blur(self, valoare_schimbare):
        noua_valoare = self.slider_blur.get() + valoare_schimbare
        noua_valoare = max(0, min(10, noua_valoare))
        self.slider_blur.set(noua_valoare)
        self.executa_recalculare_slider()

    def ajusteaza_binarizare(self, valoare_schimbare):
        noua_valoare = self.slider_prag.get() + valoare_schimbare
        noua_valoare = max(0, min(255, noua_valoare))
        self.slider_prag.set(noua_valoare)
        self.executa_recalculare_slider()

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
                self.btn_histograma.config(state=tk.NORMAL)
                
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
            img_afisare.thumbnail((1280, 720))
            
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
        fereastra_wiki.title("Wiki Scurtaturi")
        fereastra_wiki.geometry("450x500")
        fereastra_wiki.configure(bg=self.bg_main)
        
        fereastra_wiki.transient(self.root)
        
        text_wiki = tk.Text(fereastra_wiki, wrap=tk.WORD, font=("Helvetica", 10), padx=15, pady=15, bg=self.bg_panel, fg=self.fg_text, insertbackground=self.fg_text)
        text_wiki.pack(expand=True, fill=tk.BOTH)
        
        continut = """
        Comenzi Generale:
        - Ctrl + O: Deschide o imagine
        - Ctrl + S: Salveaza imaginea curenta
        - Ctrl + Z: Undo
        - Ctrl + Y: Redo
        - Ctrl + R: Reset imagine
        - Ctrl + +: Mareste dimensiunea pensulei
        - Ctrl + -: Micsoreaza dimensiunea pensulei
        - Ctrl + G: Mod Global
        - Ctrl + N: Mod Selectie
        - Ctrl + B: Mod Pensula
        - Ctrl + Left: Rotire stanga
        - Ctrl + Right: Rotire dreapta
        - Ctrl + Up: Mareste slider aberration
        - Ctrl + Down: Micsoreaza slider aberration
        
        Urmatoarele 4 functioneaza doar pe Linux:
        - Ctrl + KeyPad Up: Mareste slider blur
        - Ctrl + KeyPad Down: Micsoreaza slider blur
        - Ctrl + KeyPad Left: Micsoreaza slider binarizare
        - Ctrl + KeyPad Right: Mareste slider binarizare
        
        Filtre:
        - Ctrl + 1: Grayscale
        - Ctrl + 2: Negativare
        - Ctrl + 3: Binarizare
        - Ctrl + 4: Chromatic Aberration
        - Ctrl + 5: Blur
        - Ctrl + 6: Canny Edge Detection
        - Ctrl + 7: Sare si Piper
        """

        text_wiki.insert(tk.END, continut.strip())
        text_wiki.config(state=tk.DISABLED)

    def afiseaza_histograma(self):
        if not self.imagine_curenta:
            messagebox.showinfo("Histograma", "Deschide mai intai o imagine pentru a vedea histograma.")
            return

        img_rgb = self.imagine_curenta.convert("RGB")
        img_gray = self.imagine_curenta.convert("L")
        is_grayscale = self.imagine_curenta.mode == "L"

        fereastra_hist = tk.Toplevel(self.root)
        fereastra_hist.title("Histograma imagine")
        fereastra_hist.geometry("760x560")
        fereastra_hist.configure(bg=self.bg_main)
        fereastra_hist.transient(self.root)

        opt_frame = ttk.Frame(fereastra_hist, padding=10, style="Main.TFrame")
        opt_frame.pack(fill=tk.X)

        tk.Label(opt_frame, text="Afisare histograma:", font=("Helvetica", 10, "bold"), background=self.bg_main, foreground=self.fg_text).pack(side=tk.LEFT)
        hist_type = tk.StringVar(value="Color")

        def update_hist():
            if hist_type.get() == "Color":
                img_hist = self.creeaza_histograma_color_image(img_rgb)
            else:
                img_hist = self.creeaza_histograma_grayscale_image(img_gray)
            tk_hist = ImageTk.PhotoImage(img_hist)
            hist_label.config(image=tk_hist)
            hist_label.image = tk_hist

        tk.Radiobutton(opt_frame, text="Color", variable=hist_type, value="Color", command=update_hist, background=self.bg_main, foreground=self.fg_text, selectcolor=self.bg_panel).pack(side=tk.LEFT, padx=(15, 0))
        tk.Radiobutton(opt_frame, text="Grayscale", variable=hist_type, value="Grayscale", command=update_hist, background=self.bg_main, foreground=self.fg_text, selectcolor=self.bg_panel).pack(side=tk.LEFT, padx=10)

        hist_label = tk.Label(fereastra_hist, bg=self.bg_main)
        hist_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        update_hist()

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def creeaza_histograma_color_image(self, img_rgb):
        width = 720
        height = 480
        margin = 40
        plot_height = 320

        bg_rgb = self._hex_to_rgb(self.bg_panel)
        fg_rgb = self._hex_to_rgb(self.fg_text)
        
        img = Image.new("RGB", (width, height), bg_rgb)
        draw = ImageDraw.Draw(img)
        draw.text((margin, 10), "Histograma RGB", fill=fg_rgb)

        rgb_top = 30
        rgb_bottom = rgb_top + plot_height
        draw.rectangle((margin, rgb_top, width - margin, rgb_bottom), outline=(102, 102, 102))

        hist = img_rgb.histogram()
        hist_r = hist[0:256]
        hist_g = hist[256:512]
        hist_b = hist[512:768]
        max_rgb = max(max(hist_r), max(hist_g), max(hist_b), 1)

        for i in range(256):
            x = margin + int(i * (width - margin * 2) / 255)
            r_height = int((hist_r[i] / max_rgb) * (plot_height - 30))
            g_height = int((hist_g[i] / max_rgb) * (plot_height - 30))
            b_height = int((hist_b[i] / max_rgb) * (plot_height - 30))
            draw.line((x, rgb_bottom, x, rgb_bottom - r_height), fill=(220, 60, 60), width=2)
            draw.line((x, rgb_bottom, x, rgb_bottom - g_height), fill=(60, 200, 60), width=2)
            draw.line((x, rgb_bottom, x, rgb_bottom - b_height), fill=(60, 100, 240), width=2)

        legend_y = rgb_top + 10
        draw.rectangle((width - margin - 170, legend_y, width - margin - 20, legend_y + 70), outline=(102, 102, 102), fill=bg_rgb)
        draw.rectangle((width - margin - 160, legend_y + 8, width - margin - 140, legend_y + 24), fill=(220, 60, 60))
        draw.text((width - margin - 130, legend_y + 6), "Rosu", fill=fg_rgb)
        draw.rectangle((width - margin - 160, legend_y + 28, width - margin - 140, legend_y + 44), fill=(60, 200, 60))
        draw.text((width - margin - 130, legend_y + 26), "Verde", fill=fg_rgb)
        draw.rectangle((width - margin - 160, legend_y + 48, width - margin - 140, legend_y + 64), fill=(60, 100, 240))
        draw.text((width - margin - 130, legend_y + 46), "Albastru", fill=fg_rgb)

        return img

    def creeaza_histograma_grayscale_image(self, img_gray):
        width = 720
        height = 480
        margin = 40
        plot_height = 320

        bg_rgb = self._hex_to_rgb(self.bg_panel)
        fg_rgb = self._hex_to_rgb(self.fg_text)

        img = Image.new("RGB", (width, height), bg_rgb)
        draw = ImageDraw.Draw(img)
        draw.text((margin, 10), "Histograma grayscale", fill=fg_rgb)

        gray_top = 30
        gray_bottom = gray_top + plot_height
        draw.rectangle((margin, gray_top, width - margin, gray_bottom), outline=(102, 102, 102))

        hist_gray = img_gray.histogram()
        max_gray = max(hist_gray) or 1

        for i in range(256):
            x = margin + int(i * (width - margin * 2) / 255)
            height_gray = int((hist_gray[i] / max_gray) * (plot_height - 30))
            draw.line((x, gray_bottom, x, gray_bottom - height_gray), fill=(160, 160, 160), width=2)

        return img

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

