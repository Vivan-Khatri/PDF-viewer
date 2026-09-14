import tkinter as tk
from tkinter import filedialog, ttk

from pdf_viewer import PDFViewer
from theme import LIGHT_THEME, DARK_THEME

def make_button(parent, text, command, width=None, accent=False,
                font_size=11, bold=False, tooltip=None, **kw):
    """Create a flat-styled button consistent with the design system."""
    weight = "bold" if bold else "normal"
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=10,
        pady=5,
        font=("Segoe UI", font_size, weight),
        **kw
    )
    if width:
        btn.config(width=width)

    if tooltip:
        _add_tooltip(btn, tooltip)

    return btn


def _add_tooltip(widget, text):
    tip = None

    def enter(e):
        nonlocal tip
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tip,
            text=text,
            bg="#1F2937",
            fg="#F9FAFB",
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
            relief="flat",
            bd=0
        )
        lbl.pack()

    def leave(e):
        nonlocal tip
        if tip:
            tip.destroy()
            tip = None

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)


def make_separator(parent, colors):
    """Vertical separator for toolbar groups."""
    sep = tk.Frame(parent, width=1, bg=colors["separator"])
    sep.pack(side="left", fill="y", padx=8, pady=6)
    return sep

#Main

class PDFApplication:

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced PDF Viewer")
        self.root.geometry("1100x820")
        self.root.minsize(700, 500)

        # Theme state
        self.dark_mode = False
        self.dark_pdf = False
        self.continuous = True
        self.theme = LIGHT_THEME

        # Build UI
        self._build_toolbar()
        self._build_canvas_area()
        self._build_statusbar()

        # PDF viewer engine
        self.viewer = PDFViewer(self.canvas, self.frame)

        # Events
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.frame.bind("<Configure>", self._on_frame_configure)

        # Mouse wheel — scroll and ctrl+zoom
        self.root.bind("<MouseWheel>", self._on_mousewheel)
        self.root.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)

        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.open_pdf())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<Left>", lambda e: self.previous_page())
        self.root.bind("<Prior>", lambda e: self.previous_page())   # Page Up
        self.root.bind("<Next>", lambda e: self.next_page())        # Page Down
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self._zoom_reset())

        # Initial theme
        self.apply_theme()
        
#Toolbar

    def _build_toolbar(self):
        self.toolbar = tk.Frame(self.root, height=60)
        self.toolbar.pack(side="top", fill="x")
        self.toolbar.pack_propagate(False)

        # ---- GROUP 1: File --------------------------------
        self.open_btn = make_button(
            self.toolbar, "📂  Open PDF", self.open_pdf,
            font_size=12, bold=True,
            tooltip="Open a PDF file  (Ctrl+O)"
        )
        self.open_btn.pack(side="left", padx=(12, 4), pady=8)

        # ---- GROUP 2: Navigation --------------------------
        self._sep1 = None   # filled in apply_theme

        self.prev_btn = make_button(
            self.toolbar, "◀", self.previous_page,
            tooltip="Previous page  (←)"
        )
        self.prev_btn.pack(side="left", padx=2, pady=8)

        # Page entry + label
        self._page_frame = tk.Frame(self.toolbar)
        self._page_frame.pack(side="left", padx=4, pady=8)

        self.page_entry = tk.Entry(
            self._page_frame,
            width=4,
            justify="center",
            font=("Segoe UI", 10),
            relief="flat",
            bd=1
        )
        self.page_entry.insert(0, "0")
        self.page_entry.pack(side="left")
        self.page_entry.bind("<Return>", self._on_page_entry)

        self._page_sep = tk.Label(
            self._page_frame,
            text=" / ",
            font=("Segoe UI", 10)
        )
        self._page_sep.pack(side="left")

        self.page_total_label = tk.Label(
            self._page_frame,
            text="0",
            font=("Segoe UI", 10)
        )
        self.page_total_label.pack(side="left")

        self.next_btn = make_button(
            self.toolbar, "▶", self.next_page,
            tooltip="Next page  (→)"
        )
        self.next_btn.pack(side="left", padx=2, pady=8)

        #zoom
        self.zoom_out_btn = make_button(
            self.toolbar, "−", self.zoom_out,
            tooltip="Zoom out  (Ctrl+−)"
        )
        self.zoom_out_btn.pack(side="left", padx=2, pady=8)

        # Zoom entry
        self.zoom_entry = tk.Entry(
            self.toolbar,
            width=5,
            justify="center",
            font=("Segoe UI", 10),
            relief="flat",
            bd=1
        )
        self.zoom_entry.insert(0, "100%")
        self.zoom_entry.pack(side="left", padx=4, pady=8)
        self.zoom_entry.bind("<Return>", self._on_zoom_entry)

        self.zoom_in_btn = make_button(
            self.toolbar, "+", self.zoom_in,
            tooltip="Zoom in  (Ctrl+=)"
        )
        self.zoom_in_btn.pack(side="left", padx=2, pady=8)

        # Fit presets
        self.fit_width_btn = make_button(
            self.toolbar, "⇔ Fit Width", self.fit_width,
            tooltip="Fit page to window width"
        )
        self.fit_width_btn.pack(side="left", padx=(6, 2), pady=8)

        self.fit_page_btn = make_button(
            self.toolbar, "⛶ Fit Page", self.fit_page,
            tooltip="Fit entire page in window"
        )
        self.fit_page_btn.pack(side="left", padx=2, pady=8)

        # View toggles 
        self.theme_btn = make_button(
            self.toolbar, "🌙  Dark UI", self.toggle_theme,
            font_size=11, bold=True,
            tooltip="Toggle dark / light interface"
        )
        self.theme_btn.pack(side="right", padx=(4, 12), pady=8)

        self.dark_pdf_btn = make_button(
            self.toolbar, "🌑  Dark PDF", self.toggle_dark_pdf,
            font_size=11, bold=True,
            tooltip="Invert PDF colours for dark reading"
        )
        self.dark_pdf_btn.pack(side="right", padx=2, pady=8)

        self.scroll_mode_btn = make_button(
            self.toolbar, "≡  Continuous", self.toggle_scroll_mode,
            font_size=11, bold=True,
            tooltip="Toggle continuous / single-page mode"
        )
        self.scroll_mode_btn.pack(side="right", padx=2, pady=8)

    def _build_canvas_area(self):
        # Outer container holds canvas + both scrollbars
        self.canvas_container = tk.Frame(self.root)
        self.canvas_container.pack(side="top", fill="both", expand=True)

        # Vertical scrollbar
        self.v_scrollbar = tk.Scrollbar(
            self.canvas_container,
            orient="vertical"
        )
        self.v_scrollbar.pack(side="right", fill="y")

        # Horizontal scrollbar
        self.h_scrollbar = tk.Scrollbar(
            self.canvas_container,
            orient="horizontal"
        )
        self.h_scrollbar.pack(side="bottom", fill="x")

        # Canvas
        self.canvas = tk.Canvas(
            self.canvas_container,
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)

        # Inner frame that holds all page labels
        self.frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.frame,
            anchor="nw"
        )

        # Welcome overlay — shown until first PDF is opened
        self._welcome_id = None
        self._draw_welcome()

    
    def _build_statusbar(self):
        self.statusbar = tk.Frame(self.root, height=32)
        self.statusbar.pack(side="bottom", fill="x")
        self.statusbar.pack_propagate(False)

        self.status_filename = tk.Label(
            self.statusbar,
            text="No file open",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        self.status_filename.pack(side="left", padx=12)

        self.status_right = tk.Label(
            self.statusbar,
            text="",
            font=("Segoe UI", 10),
            anchor="e"
        )
        self.status_right.pack(side="right", padx=12)

        # Keyboard shortcut hint
        self.status_hint = tk.Label(
            self.statusbar,
            text="Ctrl+O: Open  |  ← → / PgUp PgDn: Navigate  |  Ctrl+Scroll: Zoom",
            font=("Segoe UI", 10),
            anchor="center"
        )
        self.status_hint.pack(side="left", padx=20)

    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Open PDF",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        # Remove welcome screen once a file is opened
        self._hide_welcome()

        self.viewer.dark_pdf = self.dark_pdf
        self.viewer.continuous = self.continuous
        self.viewer.open_pdf(file_path)

        # Scroll to top
        self.canvas.yview_moveto(0)

        self.update_labels()
        self._center_content()
        self._update_statusbar()

    def next_page(self):
        self.viewer.next_page()
        self.update_labels()
        self._update_statusbar()

    def previous_page(self):
        self.viewer.previous_page()
        self.update_labels()
        self._update_statusbar()

    def zoom_in(self):
        self.viewer.zoom_in()
        self.update_labels()
        self._center_content()

    def zoom_out(self):
        self.viewer.zoom_out()
        self.update_labels()
        self._center_content()

    def _zoom_reset(self):
        self.viewer.set_zoom(1.0)
        self.update_labels()
        self._center_content()

    def fit_width(self):
        w = self.canvas.winfo_width()
        self.viewer.fit_width(w)
        self.update_labels()
        self._center_content()

    def fit_page(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        self.viewer.fit_page(w, h)
        self.update_labels()
        self._center_content()

    # ----------------------------------------------------------
    # Label / entry updates
    # ----------------------------------------------------------

    def update_labels(self):
        cur, total = self.viewer.get_page_info()

        # Page entry
        self.page_entry.config(state="normal")
        self.page_entry.delete(0, "end")
        self.page_entry.insert(0, cur)

        # Page total
        self.page_total_label.config(text=total)

        # Zoom entry
        self.zoom_entry.config(state="normal")
        self.zoom_entry.delete(0, "end")
        self.zoom_entry.insert(0, f"{self.viewer.get_zoom_pct()}%")

    def _update_statusbar(self):
        fname = self.viewer.get_filename()
        self.status_filename.config(
            text=fname if fname else "No file open"
        )

        cur, total = self.viewer.get_page_info()
        zoom = self.viewer.get_zoom_pct()
        if total != "0":
            self.status_right.config(
                text=f"Page {cur} of {total}  |  Zoom: {zoom}%"
            )
        else:
            self.status_right.config(text="")

    def _on_page_entry(self, event):
        try:
            page = int(self.page_entry.get())
            self.viewer.goto_page(page)
            self.update_labels()
            self._update_statusbar()
        except ValueError:
            self.update_labels()

    def _on_zoom_entry(self, event):
        raw = self.zoom_entry.get().replace("%", "").strip()
        try:
            pct = float(raw)
            self.viewer.set_zoom(pct / 100.0)
            self.update_labels()
            self._center_content()
            self._update_statusbar()
        except ValueError:
            self.update_labels()

 
    def _on_canvas_configure(self, event=None):
        self._center_content()
        self._reposition_welcome()

    def _on_frame_configure(self, event=None):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self._center_content()

    def _center_content(self, event=None):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        canvas_w = self.canvas.winfo_width()
        frame_w = self.frame.winfo_reqwidth()

        x_margin = max(0, (canvas_w - frame_w) // 2)
        self.canvas.coords(self.canvas_window, x_margin, 0)

    def _draw_welcome(self):
        """Draw a centred welcome prompt directly on the canvas."""
        cx = self.canvas.winfo_width() // 2 or 550
        cy = self.canvas.winfo_height() // 2 or 350

        # Soft icon
        self._welcome_id = []
        self._welcome_id.append(
            self.canvas.create_text(
                cx, cy - 48,
                text="📄",
                font=("Segoe UI", 52),
                fill="#9CA3AF",
                tags="welcome"
            )
        )
        self._welcome_id.append(
            self.canvas.create_text(
                cx, cy + 20,
                text="Open a PDF to get started",
                font=("Segoe UI", 16, "bold"),
                fill="#6B7280",
                tags="welcome"
            )
        )
        self._welcome_id.append(
            self.canvas.create_text(
                cx, cy + 50,
                text="Click  📂 Open PDF  or press  Ctrl+O",
                font=("Segoe UI", 11),
                fill="#9CA3AF",
                tags="welcome"
            )
        )

    def _hide_welcome(self):
        """Remove welcome overlay items from the canvas."""
        self.canvas.delete("welcome")
        self._welcome_id = []

    def _reposition_welcome(self):
        """Re-centre welcome text when the window is resized."""
        items = self.canvas.find_withtag("welcome")
        if not items:
            return
        cx = self.canvas.winfo_width() // 2 or 550
        cy = self.canvas.winfo_height() // 2 or 350
        offsets = [-48, 20, 50]
        for item, dy in zip(items, offsets):
            self.canvas.coords(item, cx, cy + dy)

    def _on_mousewheel(self, event):
        # Don't intercept if Ctrl is held (handled by ctrl handler)
        if event.state & 0x4:
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

 
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme = DARK_THEME if self.dark_mode else LIGHT_THEME

        if self.dark_mode:
            self.theme_btn.config(text="☀  Light UI")
        else:
            self.theme_btn.config(text="🌙  Dark UI")

        self.apply_theme()

    def toggle_dark_pdf(self):
        self.dark_pdf = not self.dark_pdf
        self.viewer.set_dark_pdf(self.dark_pdf)

        if self.dark_pdf:
            self.dark_pdf_btn.config(text="☀  Light PDF")
        else:
            self.dark_pdf_btn.config(text="🌑  Dark PDF")

        self.apply_theme()

    def toggle_scroll_mode(self):
        self.continuous = not self.continuous
        self.viewer.set_continuous(self.continuous)

        if self.continuous:
            self.scroll_mode_btn.config(text="≡  Continuous")
        else:
            self.scroll_mode_btn.config(text="□  Single Page")

        self._center_content()


    def apply_theme(self):
        c = self.theme

        self.root.config(bg=c["window"])

        # Toolbar
        self.toolbar.config(bg=c["toolbar"])
        self._page_frame.config(bg=c["toolbar"])
        self._page_sep.config(bg=c["toolbar"], fg=c["text_muted"])
        self.page_total_label.config(bg=c["toolbar"], fg=c["text"])

        # Canvas area
        self.canvas_container.config(bg=c["canvas"])
        self.canvas.config(bg=c["canvas"])
        self.frame.config(bg=c["canvas"])

        # Status bar
        self.statusbar.config(bg=c["statusbar"])
        self.status_filename.config(bg=c["statusbar"], fg=c["text"])
        self.status_right.config(bg=c["statusbar"], fg=c["text_muted"])
        self.status_hint.config(bg=c["statusbar"], fg=c["text_muted"])

        # All toolbar buttons
        all_buttons = [
            self.open_btn,
            self.prev_btn,
            self.next_btn,
            self.zoom_out_btn,
            self.zoom_in_btn,
            self.fit_width_btn,
            self.fit_page_btn,
            self.theme_btn,
            self.dark_pdf_btn,
            self.scroll_mode_btn,
        ]

        for btn in all_buttons:
            btn.config(
                bg=c["button"],
                fg=c["button_fg"],
                activebackground=c["button_active"],
                activeforeground=c["button_fg"],
            )

        # Entry widgets
        for entry in [self.page_entry, self.zoom_entry]:
            entry.config(
                bg=c["entry_bg"],
                fg=c["entry_fg"],
                insertbackground=c["entry_fg"],
                disabledbackground=c["entry_bg"],
                disabledforeground=c["text_muted"],
                highlightbackground=c["entry_border"],
                highlightcolor=c["accent"],
                highlightthickness=1,
            )

        # Toolbar border (bottom line)
        self.toolbar.config(
            highlightbackground=c["toolbar_border"],
            highlightthickness=0
        )

        # Status bar top border
        self.statusbar.config(
            highlightbackground=c["statusbar_border"],
            highlightthickness=0
        )

        # Re-theme page labels inside the frame if present
        for widget in self.frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=c["canvas"])



if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(True, True)

    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = PDFApplication(root)
    root.mainloop()