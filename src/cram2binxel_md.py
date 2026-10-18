# -*- coding: utf-8 -*-
"""Genesis CRAM to Binxelview RGB24 palette converter."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_FILES = None
    TkinterDnD = tk.Tk
    DND_AVAILABLE = False


def reverse_bits(value, width):
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def convert_cram(data, byte_order="big"):
    if len(data) not in (32, 512):
        raise ValueError(
            "CRAM inválido: esperado 32 bytes (16 cores) ou 512 bytes "
            "(256 cores); recebido %d bytes." % len(data)
        )
    count = len(data) // 2
    index_bits = 4 if count == 16 else 8
    colors = []
    for offset in range(0, len(data), 2):
        word = int.from_bytes(data[offset:offset + 2], byte_order)
        # Mega Drive CRAM: 0000 BBB0 GGG0 RRR0
        r = ((word >> 1) & 7) * 255 // 7
        g = ((word >> 5) & 7) * 255 // 7
        b = ((word >> 9) & 7) * 255 // 7
        colors.append((r, g, b))

    # Index bit-reversal ordering used by this converter.
    reordered = [None] * count
    for source_index, color in enumerate(colors):
        reordered[reverse_bits(source_index, index_bits)] = color
    return bytes(channel for color in reordered for channel in color)


def convert_file(input_path, output_path, byte_order="big"):
    with open(input_path, "rb") as stream:
        data = stream.read()
    palette = convert_cram(data, byte_order)
    output_path = os.path.abspath(os.path.expanduser(output_path))
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "wb") as stream:
        stream.write(palette)
    return output_path, len(palette) // 3


BaseWindow = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class ConverterApp(BaseWindow):
    def __init__(self):
        super().__init__()
        self.title("cram2binxel_MD — CRAM to Binxelview")
        self.geometry("720x390")
        self.minsize(620, 350)
        self.configure(padx=18, pady=16)

        tk.Label(self, text="CRAM → BINXELVIEW", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(self, text="Mega Drive / Genesis CRAM → RGB24 palette (.pal)",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 16))

        fields = tk.Frame(self)
        fields.pack(fill="x")
        tk.Label(fields, text="Input", width=10, anchor="w").grid(row=0, column=0, sticky="w", pady=7)
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(fields, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=7)
        tk.Button(fields, text="Browse…", command=self.browse_input).grid(row=0, column=2, pady=7)

        tk.Label(fields, text="Output", width=10, anchor="w").grid(row=1, column=0, sticky="w", pady=7)
        self.output_var = tk.StringVar()
        self.output_entry = tk.Entry(fields, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=7)
        tk.Button(fields, text="Save as…", command=self.browse_output).grid(row=1, column=2, pady=7)
        fields.columnconfigure(1, weight=1)

        if DND_AVAILABLE:
            for widget in (self, self.input_entry):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self.on_drop)
            hint = "Drag-and-drop ativado: solte um dump CRAM no campo Input."
        else:
            hint = "Drag-and-drop opcional: instale com python -m pip install tkinterdnd2."
        tk.Label(self, text=hint, fg="#555", font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 12))

        options = tk.LabelFrame(self, text="CRAM input options", padx=10, pady=8)
        options.pack(fill="x", pady=(0, 14))
        tk.Label(options, text="Byte order:").pack(side="left")
        self.byte_order = tk.StringVar(value="big")
        tk.OptionMenu(options, self.byte_order, "big", "little").pack(side="left", padx=(8, 20))
        tk.Label(options, text="16 colors: 32 bytes | 256 colors: 512 bytes | Output: RGB24, no header",
                 fg="#555").pack(side="left")

        buttons = tk.Frame(self)
        buttons.pack(fill="x")
        tk.Button(buttons, text="Convert", command=self.convert, width=16).pack(side="right")
        tk.Button(buttons, text="Clear", command=self.clear, width=12).pack(side="right", padx=8)
        self.status = tk.Label(self, text="Ready.", anchor="w", justify="left")
        self.status.pack(fill="x", pady=(14, 0))

    def browse_input(self):
        path = filedialog.askopenfilename(
            title="Select raw CRAM dump",
            filetypes=[("CRAM / BIN", "*.bin *.dat *.cram"), ("All files", "*.*")]
        )
        if path:
            self.set_input(path)

    def browse_output(self):
        initial = self.output_var.get().strip()
        if not initial and self.input_var.get().strip():
            stem, _ = os.path.splitext(self.input_var.get().strip())
            initial = stem + "_Binxelview.pal"
        path = filedialog.asksaveasfilename(
            title="Save Binxelview palette", defaultextension=".pal",
            initialfile=os.path.basename(initial) if initial else "palette.pal",
            initialdir=os.path.dirname(initial) if initial else None,
            filetypes=[("Binxelview palette", "*.pal"), ("All files", "*.*")]
        )
        if path:
            self.output_var.set(path)

    def set_input(self, path):
        path = path.strip().strip("{}")
        self.input_var.set(path)
        stem, _ = os.path.splitext(path)
        if not self.output_var.get().strip():
            self.output_var.set(stem + "_Binxelview.pal")

    def on_drop(self, event):
        paths = self.tk.splitlist(event.data)
        if paths:
            self.set_input(paths[0])

    def clear(self):
        self.input_var.set("")
        self.output_var.set("")
        self.status.config(text="Fields cleared.")

    def convert(self):
        source = self.input_var.get().strip().strip('"')
        destination = self.output_var.get().strip().strip('"')
        if not source:
            messagebox.showwarning("Missing input", "Informe ou selecione o arquivo CRAM de entrada.")
            return
        if not destination:
            messagebox.showwarning("Missing output", "Informe o caminho do arquivo .pal de saída.")
            return
        try:
            output, count = convert_file(source, destination, self.byte_order.get())
            self.status.config(text=f"Success: {count} colors written to {output}")
            messagebox.showinfo("Conversion complete", f"{count} colors converted.\n\n{output}")
        except Exception as exc:
            self.status.config(text="Conversion failed.")
            messagebox.showerror("Conversion failed", str(exc))


if __name__ == "__main__":
    ConverterApp().mainloop()
