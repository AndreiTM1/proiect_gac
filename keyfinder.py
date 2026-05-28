#Am folosit acest script generat pentru a afla semnalele transmise de taste

import tkinter as tk

def arata_tasta(event):
    print(f"Ai apasat: {event.keysym}")
    print(f"Pentru o scurtatura simpla foloseste: <{event.keysym}>")
    print(f"Daca o combini cu Ctrl foloseste: <Control-Key-{event.keysym}>")
    print("-" * 30)

root = tk.Tk()
root.title("Afla Numele Tastei")
root.geometry("350x150")

tk.Label(root, text="Apasa orice tasta...\nUita-te in consola sa vezi cum se numeste!", 
          justify=tk.CENTER, font=("Helvetica", 11)).pack(expand=True)

# Asculta absolut orice tasta apasata
root.bind("<KeyPress>", arata_tasta)

root.mainloop()
