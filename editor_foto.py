import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter
import cv2
import numpy as np

class EditorFotoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor Foto Profesional")
        self.root.geometry("1050x800")
        
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # ARHITECTURA NOUA DE IMAGINI
        self.imagine_originala = None
        self.imagine_baza = None     # Imaginea care contine editarile permanente (pensula/selectie)
        self.imagine_curenta = None  # Imaginea finala afisata (Baza + Filtre Globale)
        self.tk_imagine = None
        
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
        
        self.filtre_globale_active = [] # Lista filtrelor activate ca toggle
        self.btn_filtre = {}            # Referinte la butoane pentru a le schimba textul
        self.slider_timer = None        # Previne lag-ul cand se trage rapid de slider
        
        self.creare_interfata()
        self.setari_scurtaturi()

    def setari_scurtaturi(self):
        self.root.bind("<Control-plus>", self.mareste_brush)
        self.root.bind("<Control-equal>", self.mareste_brush) 
        self.root.bind("<Control-minus>", self.micsoreaza_brush)
        self.root.bind("<Control-KP_Add>", self.mareste_brush)
        self.root.bind("<Control-KP_Subtract>", self.micsoreaza_brush)

    def get_functii_filtre(self):
        # Dictionar care leaga numele filtrului de functia matematica
        return {
            "Alb-Negru": lambda img: img.convert("L"),
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

        # Top Bar
        top_frame = ttk.Frame(main_frame, padding="5", relief=tk.GROOVE)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.btn_deschide = ttk.Button(top_frame, text="Deschide Poza", command=self.deschide_imagine)
        self.btn_deschide.pack(side=tk.LEFT, padx=5)

        self.btn_salveaza = ttk.Button(top_frame, text="Salveaza Poza", command=self.salveaza_imagine, state=tk.DISABLED)
        self.btn_salveaza.pack(side=tk.LEFT, padx=5)

        self.lbl_status = ttk.Label(top_frame, text="Nicio imagine incarcata. Poti muta imaginea cu Click Dreapta.", foreground="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # Panou Stanga
        left_frame = ttk.Frame(main_frame, width=240, padding="10", relief=tk.RIDGE)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(left_frame, text="Mod de Lucru", font=("Helvetica", 11, "bold")).pack(pady=(0, 5))
        self.mod_lucru = tk.StringVar(value="GLOBAL")
        
        ttk.Radiobutton(left_frame, text="Pe toata poza (Toggle)", variable=self.mod_lucru, value="GLOBAL", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(left_frame, text="Pe selectie", variable=self.mod_lucru, value="SELECTIE", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(left_frame, text="Pensula (Brush)", variable=self.mod_lucru, value="BRUSH", command=self.schimba_mod).pack(fill=tk.X)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(left_frame, text="Marime Pensula (Ctrl +/-)", font=("Helvetica", 9)).pack()
        self.slider_brush = ttk.Scale(left_frame, from_=5, to=150, variable=self.dim_brush, orient=tk.HORIZONTAL)
        self.slider_brush.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # SECTIUNEA FILTRE
        ttk.Label(left_frame, text="Setari Filtre", font=("Helvetica", 11, "bold")).pack(pady=(5, 5))

        ttk.Label(left_frame, text="Binarizare (Prag)", font=("Helvetica", 9)).pack()
        self.slider_prag = ttk.Scale(left_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_prag.set(128)
        self.slider_prag.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(left_frame, text="Aberration (Intensitate)", font=("Helvetica", 9)).pack()
        self.slider_aberration = ttk.Scale(left_frame, from_=0, to=30, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_aberration.set(10)
        self.slider_aberration.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(left_frame, text="Blur (Radius)", font=("Helvetica", 9)).pack()
        self.slider_blur = ttk.Scale(left_frame, from_=0, to=10, orient=tk.HORIZONTAL, command=self.on_slider_change)
        self.slider_blur.set(2)
        self.slider_blur.pack(fill=tk.X, pady=(0, 10))

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # BUTOANE FILTRE
        lista_filtre = ["Alb-Negru", "Negativare", "Binarizare", "Chromatic Abr.", "Blur", "Canny Edge", "Sare si Piper"]
        
        for nume in lista_filtre:
            btn = ttk.Button(left_frame, text=nume, state=tk.DISABLED, 
                             command=lambda n=nume: self.proceseaza_actiune_filtru(n))
            btn.pack(fill=tk.X, pady=2)
            self.btn_filtre[nume] = btn

        ttk.Frame(left_frame).pack(expand=True)

        self.btn_reset = ttk.Button(left_frame, text="Resetare Imagine", command=self.reseteaza_imagine, state=tk.DISABLED)
        self.btn_reset.pack(fill=tk.X, pady=(10, 0))

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

    def on_slider_change(self, val):
        # Declanseaza recalcularea cu un mic delay pentru a evita lag-ul pe Raspberry Pi
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

    def deschide_imagine(self):
        cale_fisier = filedialog.askopenfilename(
            title="Alege o imagine",
            filetypes=[("Imagini suportate", "*.png *.jpg *.jpeg *.JPG *.JPEG")]
        )
        if cale_fisier:
            try:
                self.imagine_originala = Image.open(cale_fisier)
                self.imagine_baza = self.imagine_originala.copy()
                self.filtre_globale_active.clear()
                
                for nume, btn in self.btn_filtre.items():
                    btn.config(text=nume)
                
                self.btn_salveaza.config(state=tk.NORMAL)
                self.btn_reset.config(state=tk.NORMAL)
                self.schimba_mod() 
                self.recalculeaza_imagine_globala()
                
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
        if self.imagine_originala:
            self.imagine_baza = self.imagine_originala.copy()
            self.filtre_globale_active.clear()
            self.imagine_baza_filtrata_brush = None
            
            for nume, btn in self.btn_filtre.items():
                btn.config(text=nume)
                
            self.sterge_selectia_vizuala()
            self.recalculeaza_imagine_globala()

    def recalculeaza_imagine_globala(self):
        if not self.imagine_baza: return
        
        # Aplicam filtrele globale succesiv, pornind de la baza
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
            # Sistemul Toggle (Comutator)
            if nume_filtru in self.filtre_globale_active:
                self.filtre_globale_active.remove(nume_filtru)
                self.btn_filtre[nume_filtru].config(text=nume_filtru)
            else:
                self.filtre_globale_active.append(nume_filtru)
                self.btn_filtre[nume_filtru].config(text=f"* {nume_filtru}")
            
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
                
            self.imagine_baza.paste(roi_procesat, (x1, y1))
            self.sterge_selectia_vizuala()
            self.recalculeaza_imagine_globala()
            
        elif mod == "BRUSH":
            self.nume_filtru_brush = nume_filtru
            self.lbl_status.config(text=f"Pensula incarcata cu: {nume_filtru}. Poti desena.")

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
        # Probabilitate fixa de 5% pentru a tine programul rapid si ordonat
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