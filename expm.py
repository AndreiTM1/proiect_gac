import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter, ImageEnhance
import cv2
import numpy as np
from collections import deque

class EditorFotoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📸 Photo Editor Pro")
        self.root.geometry("1800x950")
        
        self.style = ttk.Style()
        self._configurare_tema()
        
        # Undo/Redo History
        self.history = deque(maxlen=10)
        self.redo_stack = deque(maxlen=10)

        # ARHITECTURA NOUA DE IMAGINI (Smart Object)
        self.imagine_absolut_originala = None # Clona 100% pura, folosita pentru Reset
        self.imagine_originala = None         # Clona de inalta rezolutie folosita ca sursa pentru Resize
        self.imagine_baza = None              # Imaginea de lucru
        self.imagine_curenta = None           # Imaginea afisata
        self.tk_imagine = None
        self.cale_fisier_curent = None
        
        # Variabile desenare
        self.rect_id = None
        self.start_x = None
        self.start_y = None
        self.selectie_curenta = None
        self.afisaj_w = 1
        self.afisaj_h = 1
        self.zoom_level = 1.0

        # Variabile Pensula si Globale
        self.nume_filtru_brush = None
        self.brush_cursor = None
        self.dim_brush = tk.IntVar(value=30)
        self.imagine_baza_filtrata_brush = None
        self.is_brushing = False
        
        self.filtre_globale_active = [] 
        self.btn_filtre = {}            
        self.slider_timer = None
        
        # Variabile pentru controlele avansate
        self.brightness_val = tk.DoubleVar(value=1.0)
        self.contrast_val = tk.DoubleVar(value=1.0)
        self.saturation_val = tk.DoubleVar(value=1.0)
        
        self.creare_interfata()
        self.setari_scurtaturi()
    
    def _configurare_tema(self):
        """Configureaza o tema moderna si profesionala"""
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        
        # Culori profesionale
        bg_dark = "#ffffff"
        bg_medium = "#2d2d2d"
        bg_light = "#3d3d3d"
        accent_color = "#0078d4"
        text_primary = "#000000"
        text_secondary = "#000000"
        
        # Configurare Framework
        self.style.configure("TFrame", background=bg_dark)
        self.style.configure("TLabel", background=bg_dark, foreground=text_primary, font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        self.style.configure("TCheckbutton", background=bg_dark, foreground=text_primary, font=("Segoe UI", 9))
        self.style.configure("TRadiobutton", background=bg_dark, foreground=text_primary, font=("Segoe UI", 9))
        self.style.configure("TScale", background=bg_dark)
        
        # Tema pentru butoane
        self.style.map("TButton",
            background=[("active", accent_color), ("pressed", "#005a9e")],
            foreground=[("active", text_primary), ("pressed", text_primary)]
        )
        
        # Separator color
        self.style.configure("TSeparator", background=bg_light)
        
        # Label pentru titluri
        self.style.configure("Title.TLabel", font=("Segoe UI", 11, "bold"), foreground=accent_color)
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 10, "bold"), foreground=text_secondary)
        
        self.root.configure(bg=bg_dark)

    def setari_scurtaturi(self):
        self.root.bind("<Control-plus>", self.mareste_brush)
        self.root.bind("<Control-equal>", self.mareste_brush) 
        self.root.bind("<Control-minus>", self.micsoreaza_brush)
        self.root.bind("<Control-KP_Add>", self.mareste_brush)
        self.root.bind("<Control-KP_Subtract>", self.micsoreaza_brush)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-o>", lambda e: self.deschide_imagine())
        self.root.bind("<Control-s>", lambda e: self.salveaza_imagine())

    def get_functii_filtre(self):
        return {
            "Alb-Negru": lambda img: img.convert("L"),
            "Negativare": self.logica_negativ,
            "Binarizare": lambda img: self.logica_binarizare(img, int(self.slider_prag.get())),
            "Chromatic Abr.": lambda img: self.logica_aberration(img, int(self.slider_aberration.get())),
            "Blur": lambda img: img.filter(ImageFilter.GaussianBlur(radius=self.slider_blur.get())),
            "Canny Edge": self.logica_canny,
            "Sare si Piper": self.logica_sare_piper,
            "Strălucire": lambda img: self._aplica_brightness(img, self.brightness_val.get()),
            "Contrast": lambda img: self._aplica_contrast(img, self.contrast_val.get()),
            "Saturație": lambda img: self._aplica_saturation(img, self.saturation_val.get()),
        }
    
    def _aplica_brightness(self, img, factor):
        """Aplică ajustare de strălucire"""
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)
    
    def _aplica_contrast(self, img, factor):
        """Aplică ajustare de contrast"""
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)
    
    def _aplica_saturation(self, img, factor):
        """Aplică ajustare de saturație"""
        if img.mode == "L":  # Grayscale nu are saturație
            return img
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)

    def creare_interfata(self):
        """Crează interfața grafică modernă și profesională"""
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== TOOLBAR TOP (Acțiuni Principale) =====
        toolbar = ttk.Frame(main_frame, relief=tk.FLAT)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        self.btn_deschide = ttk.Button(toolbar, text="🗂 Deschide (Ctrl+O)", command=self.deschide_imagine, width=20)
        self.btn_deschide.pack(side=tk.LEFT, padx=3)

        self.btn_salveaza = ttk.Button(toolbar, text="💾 Salvează (Ctrl+S)", command=self.salveaza_imagine, state=tk.DISABLED, width=20)
        self.btn_salveaza.pack(side=tk.LEFT, padx=3)

        self.btn_undo = ttk.Button(toolbar, text="↶ Undo (Ctrl+Z)", command=self.undo, state=tk.DISABLED, width=15)
        self.btn_undo.pack(side=tk.LEFT, padx=3)

        self.btn_redo = ttk.Button(toolbar, text="↷ Redo (Ctrl+Y)", command=self.redo, state=tk.DISABLED, width=15)
        self.btn_redo.pack(side=tk.LEFT, padx=3)

        self.btn_reset = ttk.Button(toolbar, text="🔄 Reset", command=self.reseteaza_imagine, state=tk.DISABLED, width=12)
        self.btn_reset.pack(side=tk.LEFT, padx=3)

        # Status bar
        self.lbl_status = ttk.Label(toolbar, text="⏳ Nicio imagine încărcată", foreground="#b0b0b0")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # ===== MAIN CONTENT AREA =====
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # ===== LEFT PANEL (Controale) =====
        left_holder = ttk.Frame(content_frame, width=280)
        left_holder.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 8))

        # Scrollable panel
        self.left_canvas = tk.Canvas(left_holder, width=280, highlightthickness=0, bg="#1e1e1e")
        self.left_scrollbar = ttk.Scrollbar(left_holder, orient=tk.VERTICAL, command=self.left_canvas.yview)
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.left_canvas, width=280, padding="12")
        self.left_window_id = self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")
        
        self.left_frame.bind("<Configure>",
            lambda e: (self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")), self._update_left_scrollbar_visibility()))
        self.left_canvas.bind("<Configure>", self._on_canvas_configure)
        self.root.after(0, self._update_left_scrollbar_visibility)

        self.root.bind_all("<MouseWheel>", self._on_left_mousewheel)
        self.root.bind_all("<Button-4>", self._on_left_mousewheel)
        self.root.bind_all("<Button-5>", self._on_left_mousewheel)

        # --- Mod de lucru ---
        ttk.Label(self.left_frame, text="▶ Mod de Lucru", style="Title.TLabel").pack(fill=tk.X, pady=(0, 8))
        self.mod_lucru = tk.StringVar(value="GLOBAL")
        
        ttk.Radiobutton(self.left_frame, text="🌍 Global (Toată poza)", variable=self.mod_lucru, value="GLOBAL", command=self.schimba_mod).pack(fill=tk.X, pady=2)
        ttk.Radiobutton(self.left_frame, text="📐 Selecție", variable=self.mod_lucru, value="SELECTIE", command=self.schimba_mod).pack(fill=tk.X, pady=2)
        ttk.Radiobutton(self.left_frame, text="🖌 Pensula", variable=self.mod_lucru, value="BRUSH", command=self.schimba_mod).pack(fill=tk.X, pady=2)

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # --- Pensula ---
        ttk.Label(self.left_frame, text="🖌 Dimensiune Pensula", style="Title.TLabel").pack(fill=tk.X, pady=(0, 5))
        self.lbl_brush_size = ttk.Label(self.left_frame, text="30 px")
        self.lbl_brush_size.pack(anchor=tk.E)
        self.dim_brush.trace("w", lambda *args: self.lbl_brush_size.config(text=f"{self.dim_brush.get()} px"))
        self.slider_brush = ttk.Scale(self.left_frame, from_=5, to=150, variable=self.dim_brush, orient=tk.HORIZONTAL, command=lambda *a: None)
        self.slider_brush.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # --- Transformare ---
        ttk.Label(self.left_frame, text="🔀 Transformare", style="Title.TLabel").pack(fill=tk.X, pady=(0, 8))

        rot_frame = ttk.Frame(self.left_frame)
        rot_frame.pack(fill=tk.X, pady=4)
        self.btn_rot_ccw = ttk.Button(rot_frame, text="Rotire ↺ 90°", state=tk.DISABLED, command=lambda: self.roteste_imagine(90))
        self.btn_rot_ccw.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.btn_rot_cw = ttk.Button(rot_frame, text="Rotire ↻ 270°", state=tk.DISABLED, command=lambda: self.roteste_imagine(270))
        self.btn_rot_cw.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        self.var_resize = tk.BooleanVar(value=False)
        self.chk_resize = ttk.Checkbutton(self.left_frame, text="📏 Redimensionare", variable=self.var_resize, command=self.toggle_resize_ui, state=tk.DISABLED)
        self.chk_resize.pack(fill=tk.X, pady=(8, 0))

        self.frame_resize = ttk.Frame(self.left_frame)
        resize_inner = ttk.Frame(self.frame_resize)
        resize_inner.pack(fill=tk.X)
        
        ttk.Label(resize_inner, text="L:").pack(side=tk.LEFT, padx=2)
        self.entry_w = ttk.Entry(resize_inner, width=6)
        self.entry_w.pack(side=tk.LEFT, padx=2)

        ttk.Label(resize_inner, text="H:").pack(side=tk.LEFT, padx=2)
        self.entry_h = ttk.Entry(resize_inner, width=6)
        self.entry_h.pack(side=tk.LEFT, padx=2)

        self.btn_aplica_resize = ttk.Button(resize_inner, text="✓", command=self.aplica_resize, width=3)
        self.btn_aplica_resize.pack(side=tk.LEFT, padx=4)

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # --- Ajustări Avansate ---
        ttk.Label(self.left_frame, text="⚙ Ajustări Avansate", style="Title.TLabel").pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.left_frame, text="Strălucire", style="Subtitle.TLabel").pack(anchor=tk.W)
        ttk.Scale(self.left_frame, from_=0.5, to=2.0, variable=self.brightness_val, orient=tk.HORIZONTAL, command=self.on_slider_change).pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.left_frame, text="Contrast", style="Subtitle.TLabel").pack(anchor=tk.W)
        ttk.Scale(self.left_frame, from_=0.5, to=2.0, variable=self.contrast_val, orient=tk.HORIZONTAL, command=self.on_slider_change).pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.left_frame, text="Saturație", style="Subtitle.TLabel").pack(anchor=tk.W)
        ttk.Scale(self.left_frame, from_=0.0, to=2.0, variable=self.saturation_val, orient=tk.HORIZONTAL, command=self.on_slider_change).pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # --- Setări Filtre ---
        ttk.Label(self.left_frame, text="🎨 Setări Filtre", style="Title.TLabel").pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.left_frame, text="Binarizare - Prag", style="Subtitle.TLabel").pack(anchor=tk.W)
        self.slider_prag = ttk.Scale(self.left_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_prag.set(128)
        self.slider_prag.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.left_frame, text="Chromatic Aberration", style="Subtitle.TLabel").pack(anchor=tk.W)
        self.slider_aberration = ttk.Scale(self.left_frame, from_=0, to=30, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_aberration.set(10)
        self.slider_aberration.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(self.left_frame, text="Blur - Radius", style="Subtitle.TLabel").pack(anchor=tk.W)
        self.slider_blur = ttk.Scale(self.left_frame, from_=0, to=10, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_blur.set(2)
        self.slider_blur.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(self.left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # --- Butoane Filtre ---
        ttk.Label(self.left_frame, text="✨ Filtre", style="Title.TLabel").pack(fill=tk.X, pady=(0, 8))
        lista_filtre = ["Alb-Negru", "Negativare", "Binarizare", "Chromatic Abr.", "Blur", "Canny Edge", "Sare si Piper", "Strălucire", "Contrast", "Saturație"]
        
        for nume in lista_filtre:
            btn = ttk.Button(self.left_frame, text=nume, state=tk.DISABLED, 
                             command=lambda n=nume: self.proceseaza_actiune_filtru(n))
            btn.pack(fill=tk.X, pady=2)
            self.btn_filtre[nume] = btn

        ttk.Frame(self.left_frame).pack(expand=True)

        # ===== CENTRAL CANVAS AREA =====
        display_frame = ttk.Frame(content_frame, relief=tk.SUNKEN, borderwidth=2)
        display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas_imagine = tk.Canvas(display_frame, bg="#1a1a1a", cursor="crosshair")
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

    # --- ACTIUNI ROTIRE SI RESIZE (SMART OBJECT) ---
    def roteste_imagine(self, unghi):
        if not self.imagine_baza: return
        self._save_to_history()
        # Rotim atat imaginea de lucru cat si sursa de rezolutie inalta
        if unghi == 90:
            self.imagine_baza = self.imagine_baza.transpose(Image.ROTATE_90)
            self.imagine_originala = self.imagine_originala.transpose(Image.ROTATE_90)
        elif unghi == 270:
            self.imagine_baza = self.imagine_baza.transpose(Image.ROTATE_270)
            self.imagine_originala = self.imagine_originala.transpose(Image.ROTATE_270)
            
        self.sterge_selectia_vizuala()
        self.recalculeaza_imagine_globala()
        
        if self.var_resize.get():
            self.entry_w.delete(0, tk.END)
            self.entry_w.insert(0, str(self.imagine_baza.width))
            self.entry_h.delete(0, tk.END)
            self.entry_h.insert(0, str(self.imagine_baza.height))

    def toggle_resize_ui(self):
        if self.var_resize.get():
            self.frame_resize.pack(fill=tk.X, pady=2)
            if self.imagine_baza:
                self.entry_w.delete(0, tk.END)
                self.entry_w.insert(0, str(self.imagine_baza.width))
                self.entry_h.delete(0, tk.END)
                self.entry_h.insert(0, str(self.imagine_baza.height))
        else:
            self.frame_resize.pack_forget()

    def aplica_resize(self):
        if not self.imagine_baza: return
        self._save_to_history()
        try:
            new_w = int(self.entry_w.get())
            new_h = int(self.entry_h.get())
            if new_w > 0 and new_h > 0:
                try:
                    resample_filter = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_filter = Image.LANCZOS
                    
                # AICI ESTE MAGICUL: Tragem pixelii din poza originala de calitate superioara, 
                # astfel poti mari imaginea fara sa fie taiati pixelii sau blurata!
                self.imagine_baza = self.imagine_originala.resize((new_w, new_h), resample_filter)
                
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

    def dezactiveaza_filtre(self):
        for btn in self.btn_filtre.values(): btn.config(state=tk.DISABLED)

    def activeaza_filtre(self):
        if self.imagine_baza:
            for btn in self.btn_filtre.values(): btn.config(state=tk.NORMAL)

    def _save_to_history(self):
        """Salvează starea curentă în historia de undo"""
        if self.imagine_baza:
            state = {
                'imagine_baza': self.imagine_baza.copy(),
                'filtre_active': self.filtre_globale_active.copy(),
                'brightness': self.brightness_val.get(),
                'contrast': self.contrast_val.get(),
                'saturation': self.saturation_val.get(),
            }
            self.history.append(state)
            self.redo_stack.clear()
            self._update_undo_redo_buttons()

    def undo(self):
        """Revine la starea anterioară"""
        if self.history:
            # Salvează starea curentă în redo stack
            current_state = {
                'imagine_baza': self.imagine_baza.copy(),
                'filtre_active': self.filtre_globale_active.copy(),
                'brightness': self.brightness_val.get(),
                'contrast': self.contrast_val.get(),
                'saturation': self.saturation_val.get(),
            }
            self.redo_stack.append(current_state)
            
            # Restaurează starea anterioară
            state = self.history.pop()
            self.imagine_baza = state['imagine_baza'].copy()
            self.filtre_globale_active = list(state['filtre_active'])
            self.brightness_val.set(state['brightness'])
            self.contrast_val.set(state['contrast'])
            self.saturation_val.set(state['saturation'])
            
            # Actualizează butoanele de filtre
            for nume, btn in self.btn_filtre.items():
                if nume in self.filtre_globale_active:
                    btn.config(text=f"* {nume}")
                else:
                    btn.config(text=nume)
            
            self.recalculeaza_imagine_globala()
            self._update_undo_redo_buttons()

    def redo(self):
        """Repetă acțiunea anulată"""
        if self.redo_stack:
            # Salvează starea curentă în history
            current_state = {
                'imagine_baza': self.imagine_baza.copy(),
                'filtre_active': self.filtre_globale_active.copy(),
                'brightness': self.brightness_val.get(),
                'contrast': self.contrast_val.get(),
                'saturation': self.saturation_val.get(),
            }
            self.history.append(current_state)
            
            # Restaurează starea din redo stack
            state = self.redo_stack.pop()
            self.imagine_baza = state['imagine_baza'].copy()
            self.filtre_globale_active = list(state['filtre_active'])
            self.brightness_val.set(state['brightness'])
            self.contrast_val.set(state['contrast'])
            self.saturation_val.set(state['saturation'])
            
            # Actualizează butoanele de filtre
            for nume, btn in self.btn_filtre.items():
                if nume in self.filtre_globale_active:
                    btn.config(text=f"* {nume}")
                else:
                    btn.config(text=nume)
            
            self.recalculeaza_imagine_globala()
            self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        """Actualizează starea butoanelor Undo/Redo"""
        self.btn_undo.config(state=tk.NORMAL if self.history else tk.DISABLED)
        self.btn_redo.config(state=tk.NORMAL if self.redo_stack else tk.DISABLED)

    def deschide_imagine(self):
        cale_fisier = filedialog.askopenfilename(
            title="Alege o imagine",
            filetypes=[("Imagini suportate", "*.png *.jpg *.jpeg *.JPG *.JPEG")]
        )
        if cale_fisier:
            try:
                # Salvam clona absoluta a fisierului (neatinsa de transformari sau filtre)
                self.imagine_absolut_originala = Image.open(cale_fisier)
                self.imagine_originala = self.imagine_absolut_originala.copy()
                self.imagine_baza = self.imagine_originala.copy()
                self.cale_fisier_curent = cale_fisier
                self.filtre_globale_active.clear()
                self.history.clear()
                self.redo_stack.clear()
                
                for nume, btn in self.btn_filtre.items():
                    btn.config(text=nume)
                
                self.btn_salveaza.config(state=tk.NORMAL)
                self.btn_reset.config(state=tk.NORMAL)
                
                self.btn_rot_ccw.config(state=tk.NORMAL)
                self.btn_rot_cw.config(state=tk.NORMAL)
                self.chk_resize.config(state=tk.NORMAL)

                self.schimba_mod() 
                self.recalculeaza_imagine_globala()
                
                if self.var_resize.get():
                    self.entry_w.delete(0, tk.END)
                    self.entry_w.insert(0, str(self.imagine_baza.width))
                    self.entry_h.delete(0, tk.END)
                    self.entry_h.insert(0, str(self.imagine_baza.height))
                
                nume_fisier = cale_fisier.split('/')[-1]
                dims = f"{self.imagine_baza.width}×{self.imagine_baza.height}"
                self.lbl_status.config(text=f"✓ {nume_fisier} | {dims}")
                self._update_undo_redo_buttons()
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
        if self.imagine_absolut_originala:
            self._save_to_history()
            # Acum resetul reface absolut tot (dimensiune, rotatie si calitate)
            self.imagine_originala = self.imagine_absolut_originala.copy()
            self.imagine_baza = self.imagine_originala.copy()
            
            self.filtre_globale_active.clear()
            self.imagine_baza_filtrata_brush = None
            
            for nume, btn in self.btn_filtre.items():
                btn.config(text=nume)
                
            self.sterge_selectia_vizuala()
            self.recalculeaza_imagine_globala()
            
            if self.var_resize.get():
                self.entry_w.delete(0, tk.END)
                self.entry_w.insert(0, str(self.imagine_baza.width))
                self.entry_h.delete(0, tk.END)
                self.entry_h.insert(0, str(self.imagine_baza.height))

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
            self._save_to_history()
            if nume_filtru in self.filtre_globale_active:
                self.filtre_globale_active.remove(nume_filtru)
                self.btn_filtre[nume_filtru].config(text=nume_filtru)
            else:
                self.filtre_globale_active.append(nume_filtru)
                self.btn_filtre[nume_filtru].config(text=f"* {nume_filtru}")
            
            self.recalculeaza_imagine_globala()
            
        elif mod == "SELECTIE" and self.selectie_curenta:
            self._save_to_history()
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
                
            self.imagine_baza.paste(roi_procesat, (x1, y1))
            self.sterge_selectia_vizuala()
            self.recalculeaza_imagine_globala()
            
        elif mod == "BRUSH":
            self.nume_filtru_brush = nume_filtru
            self.lbl_status.config(text=f"🖌 Pensula cu: {nume_filtru}")

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