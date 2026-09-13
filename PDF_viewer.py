import tkinter as tk
from tkinter import filedialog
import fitz 
from PIL import Image, ImageTk

# --- 1. Functions to Open and Center PDF ---
def open_pdf():
    # Ask user for a file
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path: 
        return
    
    # Clear out any old pages
    for widget in frame.winfo_children(): 
        widget.destroy()
    images.clear() 
    
    # Open PDF and render pages
    doc = fitz.open(file_path)
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)) 
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        tk_img = ImageTk.PhotoImage(img)
        
        images.append(tk_img) 
        tk.Label(frame, image=tk_img, bg="gray").pack(pady=5)
        
    
    root.update_idletasks()
    center_pdf()

def center_pdf(event=None):
    """Calculates exact margins to perfectly center the document."""
    # 1. Update the scrolling boundary
    canvas.config(scrollregion=canvas.bbox("all"))
    
    # 2. Get current widths
    canvas_width = canvas.winfo_width()
    doc_width = frame.winfo_reqwidth()
    
    # 3. Calculate exact left margin (Canvas Width - Document Width) / 2
    x_margin = max(0, (canvas_width - doc_width) // 2)
    
    # 4. Move the document to sit exactly at that margin
    canvas.coords(canvas_window, x_margin, 0)

# --- 2. Basic Window Setup ---
root = tk.Tk()
root.title("Simple PDF Viewer")
root.geometry("800x800")
images = [] # Safe storage for images

tk.Button(root, text="Open PDF", command=open_pdf, font=("Arial", 12)).pack(pady=10)

# --- 3. Scrollable Canvas Setup ---
canvas = tk.Canvas(root, bg="gray")
scrollbar = tk.Scrollbar(root, command=canvas.yview)
canvas.config(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Create the inner frame and anchor it to the top-left (nw)
frame = tk.Frame(canvas, bg="gray")
canvas_window = canvas.create_window((0, 0), window=frame, anchor="nw")

# --- 4. Event Bindings ---
# Run the centering math whenever the user resizes the window
canvas.bind("<Configure>", center_pdf)
# Let the mouse wheel scroll
root.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

root.mainloop()