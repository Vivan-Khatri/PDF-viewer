
import tkinter as tk
import fitz
from PIL import Image, ImageTk, ImageOps


class PDFViewer:

    def __init__(self, canvas, frame):
        self.canvas = canvas
        self.frame = frame

        self.doc = None
        self.current_page = 0
        self.zoom = 1.0

        # Whether to render all pages at once (continuous) or one at a time
        self.continuous = True

        # Whether to invert PDF colours for dark mode
        self.dark_pdf = False

        # Keep references so Tkinter doesn't GC the images
        self.images = []

        # Cache of page labels so we can scroll to a page in continuous mode
        self._page_labels = []

  
    def open_pdf(self, file_path):
        """Open a PDF file and render it."""
        if self.doc:
            self.doc.close()

        self.doc = fitz.open(file_path)
        self.current_page = 0
        self.zoom = 1.0

        self.render()

    def render(self):
        """Dispatch to continuous or single-page rendering."""
        if not self.doc:
            return

        if self.continuous:
            self._render_all()
        else:
            self._render_single()

    def _render_single(self):
        """Render only the current page."""
        # Clear frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.images.clear()
        self._page_labels.clear()

        img = self._render_page_image(self.current_page)
        lbl = tk.Label(self.frame, image=img, bd=0, highlightthickness=0)
        lbl.pack(pady=10)

        self.images.append(img)
        self._page_labels.append(lbl)

        self._refresh_scrollregion()

    def _render_all(self):
        """Render every page stacked vertically for continuous scroll."""
        # Clear frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.images.clear()
        self._page_labels = []

        for page_num in range(len(self.doc)):
            img = self._render_page_image(page_num)
            lbl = tk.Label(
                self.frame,
                image=img,
                bd=2,
                relief="flat",
                highlightthickness=0
            )
            lbl.pack(pady=8)

            self.images.append(img)
            self._page_labels.append(lbl)

        self._refresh_scrollregion()

    def _render_page_image(self, page_num):
        """Render a single PDF page to a Tkinter PhotoImage."""
        page = self.doc[page_num]

        matrix = fitz.Matrix(2.0 * self.zoom, 2.0 * self.zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if self.dark_pdf:
            img = self._apply_dark_mode(img)

        return ImageTk.PhotoImage(img)

    def _apply_dark_mode(self, img):
        """Invert image and apply a subtle warm tint for dark PDF mode."""
        inverted = ImageOps.invert(img)
        return inverted

    def _refresh_scrollregion(self):
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

  
    def next_page(self):
        if not self.doc:
            return

        if self.continuous:
            # Scroll so the next page top is visible
            if self.current_page < len(self.doc) - 1:
                self.current_page += 1
                self._scroll_to_page(self.current_page)
        else:
            if self.current_page < len(self.doc) - 1:
                self.current_page += 1
                self.render()

    def previous_page(self):
        if not self.doc:
            return

        if self.continuous:
            if self.current_page > 0:
                self.current_page -= 1
                self._scroll_to_page(self.current_page)
        else:
            if self.current_page > 0:
                self.current_page -= 1
                self.render()

    def goto_page(self, page_num):
        """Jump directly to a page (1-indexed from UI)."""
        if not self.doc:
            return

        page_num = max(1, min(page_num, len(self.doc)))
        self.current_page = page_num - 1

        if self.continuous:
            self._scroll_to_page(self.current_page)
        else:
            self.render()

    def _scroll_to_page(self, page_index):
        """Scroll the canvas so the given page is at the top."""
        if page_index >= len(self._page_labels):
            return

        lbl = self._page_labels[page_index]
        lbl.update_idletasks()

        # y position of the label relative to the canvas content
        lbl_y = lbl.winfo_y()

        total_height = self.frame.winfo_reqheight()

        if total_height <= 0:
            return

        fraction = lbl_y / total_height
        self.canvas.yview_moveto(fraction)

 
    def zoom_in(self):
        if not self.doc:
            return

        self.zoom = min(self.zoom + 0.2, 5.0)
        self.render()

    def zoom_out(self):
        if not self.doc:
            return

        self.zoom = max(self.zoom - 0.2, 0.2)
        self.render()

    def set_zoom(self, value):
        """Set zoom to an exact float (e.g. 1.0 = 100%)."""
        if not self.doc:
            return

        self.zoom = max(0.2, min(value, 5.0))
        self.render()

    def fit_width(self, canvas_width):
        """Zoom so the current page fits the canvas width."""
        if not self.doc:
            return

        page = self.doc[self.current_page]
        # page.rect.width is in PDF points; rendered at 2.0*zoom scale
        page_width_at_1 = page.rect.width * 2.0
        target_zoom = (canvas_width - 40) / page_width_at_1

        self.zoom = max(0.2, min(round(target_zoom, 2), 5.0))
        self.render()

    def fit_page(self, canvas_width, canvas_height):
        """Zoom so the full page fits the canvas (both axes)."""
        if not self.doc:
            return

        page = self.doc[self.current_page]
        w = page.rect.width * 2.0
        h = page.rect.height * 2.0

        zoom_w = (canvas_width - 40) / w
        zoom_h = (canvas_height - 40) / h

        self.zoom = max(0.2, min(round(min(zoom_w, zoom_h), 2), 5.0))
        self.render()

  
    def set_continuous(self, value: bool):
        self.continuous = value
        self.render()

        if value and self.doc:
            self._scroll_to_page(self.current_page)

    def set_dark_pdf(self, value: bool):
        self.dark_pdf = value
        self.render()


    def get_page_count(self):
        return len(self.doc) if self.doc else 0

    def get_page_info(self):
        if not self.doc:
            return "0", "0"

        return str(self.current_page + 1), str(len(self.doc))

    def get_zoom_pct(self):
        return int(self.zoom * 100)

    def get_filename(self):
        if not self.doc:
            return ""

        return self.doc.name.split("\\")[-1].split("/")[-1]