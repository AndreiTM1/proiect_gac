import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw
import cv2
import numpy as np

class EditorFotoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor Foto (Neactivat - 25 Zile Ramase)")
        self.root.geometry("1000x750")
        
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.imagine_originala = None
        self.imagine_curenta = None
        self.tk_imagine = None
        
        # Variabile pentru desenare/selectie
        self.rect_id = None
        self.start_x = None
        self.start_y = None
        self.selectie_curenta = None
        self.afisaj_w = 1
        self.afisaj_h = 1

        # Variabile pentru Brush Tool
        self.filtru_activ_brush = None
        self.brush_cursor = None
        self.dim_brush = tk.IntVar(value=30)
        self.imagine_filtrata_brush = None
        self.is_brushing = False
        
        self.creare_interfata()
        self.setari_scurtaturi()

    def setari_scurtaturi(self):
        self.root.bind("<Control-plus>", self.mareste_brush)
        self.root.bind("<Control-equal>", self.mareste_brush) 
        self.root.bind("<Control-minus>", self.micsoreaza_brush)
        self.root.bind("<Control-KP_Add>", self.mareste_brush)
        self.root.bind("<Control-KP_Subtract>", self.micsoreaza_brush)

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

        self.lbl_status = ttk.Label(top_frame, text="Nicio imagine incarcata. Poti muta imaginea cu Click Dreapta (Pan).", foreground="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # Panou Stanga (Filtre si Optiuni)
        left_frame = ttk.Frame(main_frame, width=220, padding="10", relief=tk.RIDGE)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Moduri de lucru
        ttk.Label(left_frame, text="Mod de Lucru", font=("Helvetica", 11, "bold")).pack(pady=(0, 5))
        self.mod_lucru = tk.StringVar(value="GLOBAL")
        
        ttk.Radiobutton(left_frame, text="Pe toata poza", variable=self.mod_lucru, value="GLOBAL", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(left_frame, text="Pe selectie", variable=self.mod_lucru, value="SELECTIE", command=self.schimba_mod).pack(fill=tk.X)
        ttk.Radiobutton(left_frame, text="Pensula (Brush)", variable=self.mod_lucru, value="BRUSH", command=self.schimba_mod).pack(fill=tk.X)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Optiuni Pensula
        ttk.Label(left_frame, text="Marime Pensula (Ctrl +/-)").pack()
        self.slider_brush = ttk.Scale(left_frame, from_=5, to=150, variable=self.dim_brush, orient=tk.HORIZONTAL)
        self.slider_brush.pack(fill=tk.X, pady=5)

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Filtre Standard
        ttk.Label(left_frame, text="Filtre Standard", font=("Helvetica", 11, "bold")).pack(pady=(5, 5))

        self.btn_grayscale = ttk.Button(left_frame, text="Alb-Negru", state=tk.DISABLED, 
                                        command=lambda: self.proceseaza_actiune_filtru("Alb-Negru", lambda img: img.convert("L")))
        self.btn_grayscale.pack(fill=tk.X, pady=3)

        self.btn_negativ = ttk.Button(left_frame, text="Negativare", state=tk.DISABLED,
                                      command=lambda: self.proceseaza_actiune_filtru("Negativare", self.logica_negativ))
        self.btn_negativ.pack(fill=tk.X, pady=3)

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Binarizare
        ttk.Label(left_frame, text="Binarizare (Prag)", font=("Helvetica", 10)).pack()
        self.slider_prag = ttk.Scale(left_frame, from_=0, to=255, orient=tk.HORIZONTAL)
        self.slider_prag.set(128)
        self.slider_prag.pack(fill=tk.X, pady=5)

        self.btn_binarizare = ttk.Button(left_frame, text="Aplica Binarizare", state=tk.DISABLED,
                                         command=lambda: self.proceseaza_actiune_filtru("Binarizare", 
                                                         lambda img: self.logica_binarizare(img, int(self.slider_prag.get()))))
        self.btn_binarizare.pack(fill=tk.X, pady=3)

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Efecte Speciale
        ttk.Label(left_frame, text="Efecte Speciale", font=("Helvetica", 11, "bold")).pack(pady=(0, 5))

        self.btn_aberration = ttk.Button(left_frame, text="Chromatic Aberration", state=tk.DISABLED,
                                         command=lambda: self.proceseaza_actiune_filtru("Chromatic Aberration", self.logica_aberration))
        self.btn_aberration.pack(fill=tk.X, pady=3)

        self.btn_canny = ttk.Button(left_frame, text="Detectie Contur (Canny)", state=tk.DISABLED,
                                    command=lambda: self.proceseaza_actiune_filtru("Canny Edge", self.logica_canny))
        self.btn_canny.pack(fill=tk.X, pady=3)

        ttk.Frame(left_frame).pack(expand=True)

        self.btn_reset = ttk.Button(left_frame, text="Resetare Imagine", command=self.reseteaza_imagine, state=tk.DISABLED)
        self.btn_reset.pack(fill=tk.X, pady=(10, 0))

        # Zona Centrala
        display_frame = ttk.Frame(main_frame, relief=tk.SUNKEN)
        display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas_imagine = tk.Canvas(display_frame, bg="#2e2e2e", cursor="cross")
        self.canvas_imagine.pack(expand=True, fill=tk.BOTH)

        # Evenimente mouse standard
        self.canvas_imagine.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas_imagine.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas_imagine.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas_imagine.bind("<Motion>", self.on_mouse_motion)
        self.canvas_imagine.bind("<Leave>", self.on_mouse_leave)

        # Evenimente mouse pentru rearanjare imagine (Pan)
        # Mouse Mijloc (Scroll click) sau Click Dreapta in functie de OS si preferinte
        self.canvas_imagine.bind("<ButtonPress-2>", self.start_pan)
        self.canvas_imagine.bind("<B2-Motion>", self.do_pan)
        self.canvas_imagine.bind("<ButtonPress-3>", self.start_pan)
        self.canvas_imagine.bind("<B3-Motion>", self.do_pan)

    def mareste_brush(self, event=None):
        val_noua = min(150, self.dim_brush.get() + 5)
        self.dim_brush.set(val_noua)
        if event and hasattr(event, 'x'):
            self.actualizeaza_cerc_brush(event.x, event.y)

    def micsoreaza_brush(self, event=None):
        val_noua = max(5, self.dim_brush.get() - 5)
        self.dim_brush.set(val_noua)
        if event and hasattr(event, 'x'):
            self.actualizeaza_cerc_brush(event.x, event.y)

    def schimba_mod(self):
        self.sterge_selectia_vizuala()
        self.filtru_activ_brush = None
        self.imagine_filtrata_brush = None
        self.is_brushing = False
        
        if self.brush_cursor:
            self.canvas_imagine.delete(self.brush_cursor)
            self.brush_cursor = None

        if not self.imagine_curenta:
            return

        mod = self.mod_lucru.get()
        if mod == "BRUSH":
            self.lbl_status.config(text="Mod Pensula: Alege un filtru pentru a incarca pensula.")
            self.activeaza_filtre()
        elif mod == "SELECTIE":
            self.lbl_status.config(text="Mod Selectie: Traseaza un chenar pe poza.")
            self.dezactiveaza_filtre()
        else:
            self.lbl_status.config(text="Mod Global: Filtrele se aplica pe toata poza.")
            self.activeaza_filtre()

    def dezactiveaza_filtre(self):
        for btn in [self.btn_grayscale, self.btn_negativ, self.btn_binarizare, self.btn_aberration, self.btn_canny]:
            btn.config(state=tk.DISABLED)

    def activeaza_filtre(self):
        if self.imagine_curenta:
            for btn in [self.btn_grayscale, self.btn_negativ, self.btn_binarizare, self.btn_aberration, self.btn_canny]:
                btn.config(state=tk.NORMAL)

    def deschide_imagine(self):
        cale_fisier = filedialog.askopenfilename(
            title="Alege o imagine",
            filetypes=[("Imagini suportate", "*.png *.jpg *.jpeg *.JPG *.JPEG")]
        )
        if cale_fisier:
            try:
                self.imagine_originala = Image.open(cale_fisier)
                self.imagine_curenta = self.imagine_originala.copy()
                self.actualizeaza_afisaj()
                self.btn_salveaza.config(state=tk.NORMAL)
                self.btn_reset.config(state=tk.NORMAL)
                self.schimba_mod() 
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
            self.imagine_curenta = self.imagine_originala.copy()
            self.imagine_filtrata_brush = None  # Resetam doar imaginea filtrata din memorie
            self.sterge_selectia_vizuala()
            self.actualizeaza_afisaj()
            # FARA self.schimba_mod(), astfel setarile UI curente si filtrul incarcat pe pensula NU se pierd!

    def actualizeaza_afisaj(self):
        if self.imagine_curenta:
            img_afisare = self.imagine_curenta.copy()
            img_afisare.thumbnail((750, 600))
            
            self.afisaj_w = img_afisare.width
            self.afisaj_h = img_afisare.height
            
            self.tk_imagine = ImageTk.PhotoImage(img_afisare)
            
            self.canvas_imagine.delete("img_tag")
            self.canvas_imagine.config(scrollregion=(0, 0, self.afisaj_w, self.afisaj_h))
            self.canvas_imagine.create_image(0, 0, anchor=tk.NW, image=self.tk_imagine, tags="img_tag")
            self.canvas_imagine.tag_lower("img_tag")
            
            if self.brush_cursor:
                self.canvas_imagine.tag_raise(self.brush_cursor)

    # --- PAN (REARANJARE IMAGINE) ---
    def start_pan(self, event):
        self.canvas_imagine.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas_imagine.scan_dragto(event.x, event.y, gain=1)

    # --- EVENIMENTE MOUSE ADAPTATE PENTRU COORDONATELE CANVAS ---
    def on_mouse_press(self, event):
        if not self.imagine_curenta: return
        mod = self.mod_lucru.get()
        
        # Preluam coordonatele in raport cu canvasul miscat, nu doar fereastra
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
        elif mod == "BRUSH" and self.filtru_activ_brush:
            # Recream sursa statica filtrata daca s-a dat click din nou sau s-a dat reset
            self.imagine_filtrata_brush = self.filtru_activ_brush(self.imagine_curenta)
            if self.imagine_curenta.mode != self.imagine_filtrata_brush.mode:
                self.imagine_filtrata_brush = self.imagine_filtrata_brush.convert(self.imagine_curenta.mode)
            
            self.is_brushing = True
            self.aplica_brush(cx, cy)

    def on_mouse_drag(self, event):
        if not self.imagine_curenta: return
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
        if not self.imagine_curenta: return
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
            self.imagine_filtrata_brush = None

    def on_mouse_motion(self, event):
        if self.mod_lucru.get() == "BRUSH":
            self.actualizeaza_cerc_brush(event.x, event.y)

    def on_mouse_leave(self, event):
        if self.brush_cursor:
            self.canvas_imagine.delete(self.brush_cursor)
            self.brush_cursor = None

    def actualizeaza_cerc_brush(self, window_x, window_y):
        if self.brush_cursor:
            self.canvas_imagine.delete(self.brush_cursor)
            
        cx = self.canvas_imagine.canvasx(window_x)
        cy = self.canvas_imagine.canvasy(window_y)
        r = self.dim_brush.get()
        
        # Cursorul este actualizat la coordonatele re-mapate ale canvasului
        if 0 <= cx <= self.afisaj_w and 0 <= cy <= self.afisaj_h:
            self.brush_cursor = self.canvas_imagine.create_oval(
                cx - r, cy - r, cx + r, cy + r, outline="white", dash=(2, 2)
            )

    def sterge_selectia_vizuala(self):
        if self.rect_id:
            self.canvas_imagine.delete(self.rect_id)
            self.rect_id = None
        self.selectie_curenta = None

    def proceseaza_actiune_filtru(self, nume_filtru, functie_logica):
        if not self.imagine_curenta: return
        mod = self.mod_lucru.get()

        if mod == "GLOBAL":
            self.imagine_curenta = functie_logica(self.imagine_curenta)
            self.actualizeaza_afisaj()
        
        elif mod == "SELECTIE" and self.selectie_curenta:
            raport_w = self.imagine_curenta.width / self.afisaj_w
            raport_h = self.imagine_curenta.height / self.afisaj_h
            
            x1, y1, x2, y2 = self.selectie_curenta
            x1, y1 = max(0, int(x1 * raport_w)), max(0, int(y1 * raport_h))
            x2, y2 = min(self.imagine_curenta.width, int(x2 * raport_w)), min(self.imagine_curenta.height, int(y2 * raport_h))
            
            roi = self.imagine_curenta.crop((x1, y1, x2, y2))
            roi_procesat = functie_logica(roi)
            
            if self.imagine_curenta.mode != roi_procesat.mode:
                roi_procesat = roi_procesat.convert(self.imagine_curenta.mode)
                
            self.imagine_curenta.paste(roi_procesat, (x1, y1))
            self.actualizeaza_afisaj()
            self.sterge_selectia_vizuala() # Curatam chenarul ca sa vedem clar rezultatul
            
        elif mod == "BRUSH":
            self.filtru_activ_brush = functie_logica
            self.lbl_status.config(text=f"Pensula incarcata cu: {nume_filtru}. Trage pe imagine pentru a aplica.")

    def aplica_brush(self, cx, cy):
        if not self.imagine_filtrata_brush:
            return

        raport_w = self.imagine_curenta.width / self.afisaj_w
        raport_h = self.imagine_curenta.height / self.afisaj_h
        
        orig_x = int(cx * raport_w)
        orig_y = int(cy * raport_h)
        orig_r = int(self.dim_brush.get() * max(raport_w, raport_h)) 
        
        left = max(0, orig_x - orig_r)
        upper = max(0, orig_y - orig_r)
        right = min(self.imagine_curenta.width, orig_x + orig_r)
        lower = min(self.imagine_curenta.height, orig_y + orig_r)
        
        if left >= right or upper >= lower:
            return

        roi_procesat = self.imagine_filtrata_brush.crop((left, upper, right, lower))
        
        mask = Image.new("L", (right - left, lower - upper), 0)
        draw = ImageDraw.Draw(mask)
        c_x, c_y = orig_x - left, orig_y - upper
        draw.ellipse((c_x - orig_r, c_y - orig_r, c_x + orig_r, c_y + orig_r), fill=255)
        
        self.imagine_curenta.paste(roi_procesat, (left, upper), mask)
        self.actualizeaza_afisaj()

    # --- FUNCTII FILTRE INDIVIDUALE ---
    def logica_negativ(self, img):
        if img.mode == "RGBA":
            r, g, b, a = img.split()
            img_rgb = Image.merge("RGB", (r, g, b))
            img_inversata = ImageOps.invert(img_rgb)
            r2, g2, b2 = img_inversata.split()
            return Image.merge("RGBA", (r2, g2, b2, a))
        else:
            if img.mode == '1': 
                img = img.convert("L")
            return ImageOps.invert(img)

    def logica_binarizare(self, img, prag):
        img_gri = img.convert("L")
        return img_gri.point(lambda p: 255 if p > prag else 0)

    def logica_aberration(self, img):
        img_rgb = img.convert("RGB")
        r, g, b = img_rgb.split()
        latime, inaltime = img_rgb.size
        deplasare = 10
        r_shift = r.transform((latime, inaltime), Image.AFFINE, (1, 0, deplasare, 0, 1, 0))
        b_shift = b.transform((latime, inaltime), Image.AFFINE, (1, 0, -deplasare, 0, 1, 0))
        return Image.merge("RGB", (r_shift, g, b_shift))

    def logica_canny(self, img):
        img_array = np.array(img.convert("RGB"))
        img_gri_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        contururi = cv2.Canny(img_gri_cv2, 100, 200)
        return Image.fromarray(contururi)

if __name__ == "__main__":
    root = tk.Tk()
    app = EditorFotoApp(root)
    root.mainloop()