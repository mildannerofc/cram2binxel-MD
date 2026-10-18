# -*- coding: utf-8 -*-
"""Mega Drive / Genesis CRAM dump to Binxelview RGB24 palette."""
import os
import sys
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

# Drag-and-drop is optional. Even a broken tkinterdnd2 installation must not
# prevent the regular Tkinter application from opening.
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_IMPORT_OK = True
except Exception:  # tkinterdnd2 can fail for reasons other than ImportError
    DND_FILES = None
    TkinterDnD = None
    DND_IMPORT_OK = False

COLORS_PER_LINE = 16
BYTES_PER_COLOR = 2
BYTES_PER_LINE = COLORS_PER_LINE * BYTES_PER_COLOR


def reverse_bits(value, width):
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def inspect_cram(data):
    if not data:
        raise ValueError("O arquivo de entrada está vazio.")
    if len(data) % BYTES_PER_COLOR:
        raise ValueError(
            f"O arquivo tem {len(data)} bytes. O tamanho precisa ser múltiplo de 2 "
            "para conter palavras CRAM completas."
        )
    total_colors = len(data) // BYTES_PER_COLOR
    complete_lines, partial_colors = divmod(total_colors, COLORS_PER_LINE)
    return {
        "bytes": len(data),
        "colors": total_colors,
        "complete_lines": complete_lines,
        "partial_colors": partial_colors,
        "total_lines": complete_lines + bool(partial_colors),
    }


def decode_color(word):
    # Mega Drive CRAM word: 0000 BBB0 GGG0 RRR0
    r3 = (word >> 1) & 7
    g3 = (word >> 5) & 7
    b3 = (word >> 9) & 7
    return tuple((v * 255 + 3) // 7 for v in (r3, g3, b3))


def decode_line(line_data, byte_order="big"):
    if byte_order not in ("big", "little"):
        raise ValueError("A ordem dos bytes deve ser 'big' ou 'little'.")
    if len(line_data) % 2:
        raise ValueError("Linha CRAM incompleta: faltam bytes para uma palavra de 16 bits.")
    if len(line_data) > BYTES_PER_LINE:
        raise ValueError("Uma linha CRAM não pode conter mais de 32 bytes.")
    return [
        decode_color(int.from_bytes(line_data[i:i + 2], byte_order))
        for i in range(0, len(line_data), 2)
    ]


def reorder_binxelview_line(colors):
    # Established 16-index arrangement: 0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15.
    # A partial last line is kept in source order (there are missing index slots).
    if len(colors) != COLORS_PER_LINE:
        return list(colors)
    ordered = [None] * COLORS_PER_LINE
    for source_index, color in enumerate(colors):
        ordered[reverse_bits(source_index, 4)] = color
    return ordered


def convert_cram(data, byte_order="big", selected_line=0,
                 export_mode="selected"):
    info = inspect_cram(data)
    if export_mode not in ("selected", "all"):
        raise ValueError("Modo de exportação inválido.")
    if export_mode == "selected":
        if not 0 <= selected_line < info["total_lines"]:
            raise ValueError(f"Linha inválida. Escolha entre 1 e {info['total_lines']}.")
        line_indices = [selected_line]
    else:
        line_indices = range(info["total_lines"])

    output = bytearray()
    for line_index in line_indices:
        start = line_index * BYTES_PER_LINE
        end = min(start + BYTES_PER_LINE, len(data))
        colors = decode_line(data[start:end], byte_order)
        for red, green, blue in reorder_binxelview_line(colors):
            output.extend((red, green, blue))
    return bytes(output)


def convert_file(input_path, output_path, byte_order="big",
                 selected_line=0, export_mode="selected"):
    with open(input_path, "rb") as stream:
        data = stream.read()
    info = inspect_cram(data)
    palette = convert_cram(data, byte_order, selected_line, export_mode)
    destination = os.path.abspath(os.path.expanduser(output_path))
    parent = os.path.dirname(destination)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(destination, "wb") as stream:
        stream.write(palette)
    return destination, len(palette) // 3, info


class ConverterApp:
    """Owns a Tk root; safely falls back to standard Tk if TkDnD won't load."""

    def __init__(self):
        self.dnd_enabled = False
        self.dnd_warning = ""
        if DND_IMPORT_OK:
            try:
                self.root = TkinterDnD.Tk()
                self.dnd_enabled = True
            except Exception as exc:
                self.root = tk.Tk()
                self.dnd_warning = f"Arrastar e soltar desativado: {exc}"
        else:
            self.root = tk.Tk()
            self.dnd_warning = "Arrastar e soltar opcional não está disponível."

        self.root.title("cram2binxel_MD — CRAM to Binxelview")
        self.root.geometry("790x535")
        self.root.minsize(700, 490)
        self.root.configure(padx=18, pady=16)
        self.detected_info = None
        self._build_ui()

    def mainloop(self):
        self.root.mainloop()

    def _build_ui(self):
        root = self.root
        tk.Label(root, text="CRAM → BINXELVIEW", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(root, text="Conversor de dumps CRAM do Mega Drive / Genesis para paletas RGB24 (.pal).",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 14))

        paths = tk.Frame(root)
        paths.pack(fill="x")
        tk.Label(paths, text="Input", width=10, anchor="w").grid(row=0, column=0, sticky="w", pady=6)
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(paths, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        tk.Button(paths, text="Browse…", command=self.browse_input, width=12).grid(row=0, column=2, pady=6)

        tk.Label(paths, text="Output", width=10, anchor="w").grid(row=1, column=0, sticky="w", pady=6)
        self.output_var = tk.StringVar()
        tk.Entry(paths, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        tk.Button(paths, text="Save as…", command=self.browse_output, width=12).grid(row=1, column=2, pady=6)
        paths.columnconfigure(1, weight=1)

        if self.dnd_enabled:
            try:
                for widget in (root, self.input_entry):
                    widget.drop_target_register(DND_FILES)
                    widget.dnd_bind("<<Drop>>", self.on_drop)
                drag_hint = "Arraste um arquivo CRAM para o campo Input."
            except Exception as exc:
                self.dnd_enabled = False
                drag_hint = f"Arrastar e soltar desativado; use Browse. ({exc})"
        else:
            drag_hint = self.dnd_warning or "Use Browse para selecionar o arquivo."
        tk.Label(root, text=drag_hint, fg="#666", font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 10))

        options = tk.LabelFrame(root, text="CRAM detection and conversion", padx=12, pady=10)
        options.pack(fill="x")
        top = tk.Frame(options)
        top.pack(fill="x")
        tk.Label(top, text="Byte order:").pack(side="left")
        self.byte_order = tk.StringVar(value="big")
        tk.OptionMenu(top, self.byte_order, "big", "little").pack(side="left", padx=(6, 16))
        tk.Button(top, text="Detect lines", command=self.detect).pack(side="left")
        self.detect_label = tk.Label(top, text="Nenhum arquivo analisado.", fg="#555")
        self.detect_label.pack(side="left", padx=12)

        mode_row = tk.Frame(options)
        mode_row.pack(fill="x", pady=(12, 7))
        tk.Label(mode_row, text="Export:").pack(side="left")
        self.export_mode = tk.StringVar(value="selected")
        tk.Radiobutton(mode_row, text="Preferred line only", variable=self.export_mode,
                       value="selected", command=self.update_line_controls).pack(side="left", padx=(8, 12))
        tk.Radiobutton(mode_row, text="All detected lines", variable=self.export_mode,
                       value="all", command=self.update_line_controls).pack(side="left")

        line_row = tk.Frame(options)
        line_row.pack(fill="x")
        tk.Label(line_row, text="Preferred line:").pack(side="left")
        self.line_var = tk.StringVar(value="1")
        self.line_menu = tk.OptionMenu(line_row, self.line_var, "1")
        self.line_menu.pack(side="left", padx=8)
        tk.Label(line_row, text="(1-based; one line = 16 colors / 32 bytes)", fg="#666").pack(side="left")
        self.partial_label = tk.Label(options, text="", justify="left", anchor="w",
                                       fg="#8A5A00", wraplength=720)
        self.partial_label.pack(fill="x", pady=(8, 0))
        tk.Label(options, text=("O detector conta blocos de 32 bytes. A última linha pode ser parcial; "
                               "ela é exportada sem preencher cores ausentes."),
                 justify="left", wraplength=720, fg="#555", font=("Segoe UI", 8)).pack(anchor="w", pady=(8, 0))

        buttons = tk.Frame(root)
        buttons.pack(fill="x", pady=(16, 0))
        tk.Button(buttons, text="Convert", command=self.convert, width=16).pack(side="right")
        tk.Button(buttons, text="Clear", command=self.clear, width=12).pack(side="right", padx=8)
        self.status = tk.Label(root, text="Pronto. Selecione um dump CRAM e clique em Detect lines.",
                               anchor="w", justify="left", wraplength=740)
        self.status.pack(fill="x", pady=(14, 0))

    def browse_input(self):
        path = filedialog.askopenfilename(title="Selecionar dump CRAM",
                filetypes=[("CRAM / BIN", "*.bin *.dat *.cram"), ("Todos os arquivos", "*.*")])
        if path:
            self.set_input(path)

    def browse_output(self):
        current = self.output_var.get().strip()
        path = filedialog.asksaveasfilename(title="Salvar paleta Binxelview", defaultextension=".pal",
                initialfile=os.path.basename(current) if current else "palette.pal",
                initialdir=os.path.dirname(current) if current else None,
                filetypes=[("Paleta Binxelview", "*.pal"), ("Todos os arquivos", "*.*")])
        if path:
            self.output_var.set(path)

    def set_input(self, path):
        path = path.strip().strip("{}").strip('"')
        self.input_var.set(path)
        stem, _ = os.path.splitext(path)
        if not self.output_var.get().strip():
            self.output_var.set(stem + "_Binxelview.pal")
        self.detect(show_errors=False)

    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        if paths:
            self.set_input(paths[0])

    def detect(self, show_errors=True):
        source = self.input_var.get().strip().strip('"')
        if not source:
            if show_errors:
                messagebox.showwarning("Input ausente", "Informe ou selecione um arquivo CRAM.")
            return
        try:
            with open(source, "rb") as stream:
                data = stream.read()
            info = inspect_cram(data)
            self.detected_info = info
            labels = []
            for row in range(info["total_lines"]):
                start = row * COLORS_PER_LINE
                count = min(COLORS_PER_LINE, info["colors"] - start)
                labels.append(f"{row + 1} ({count} cores)" if count != COLORS_PER_LINE else str(row + 1))
            menu = self.line_menu["menu"]
            menu.delete(0, "end")
            for index, label in enumerate(labels):
                menu.add_command(label=label, command=lambda i=index: self.line_var.set(str(i + 1)))
            self.line_var.set("1")
            self.detect_label.config(text=f"{info['colors']} cores · {info['total_lines']} linha(s)")
            if info["partial_colors"]:
                self.partial_label.config(text=f"A última linha contém {info['partial_colors']} de 16 cores; será exportada sem reordenação.")
            else:
                self.partial_label.config(text="Todas as linhas detectadas estão completas.")
            self.status.config(text=f"Arquivo analisado: {info['bytes']} bytes · {info['complete_lines']} linha(s) completa(s)" +
                               (f" + 1 parcial ({info['partial_colors']} cores)." if info["partial_colors"] else "."))
            self.update_line_controls()
        except Exception as exc:
            self.detected_info = None
            self.detect_label.config(text="Falha na detecção.")
            self.partial_label.config(text="")
            self.status.config(text=str(exc))
            if show_errors:
                messagebox.showerror("Falha ao detectar CRAM", str(exc))

    def update_line_controls(self):
        state = "normal" if self.export_mode.get() == "selected" and self.detected_info else "disabled"
        self.line_menu.config(state=state)

    def clear(self):
        self.input_var.set("")
        self.output_var.set("")
        self.detected_info = None
        self.detect_label.config(text="Nenhum arquivo analisado.")
        self.partial_label.config(text="")
        menu = self.line_menu["menu"]
        menu.delete(0, "end")
        menu.add_command(label="1", command=lambda: self.line_var.set("1"))
        self.line_var.set("1")
        self.update_line_controls()
        self.status.config(text="Campos limpos.")

    def convert(self):
        source = self.input_var.get().strip().strip('"')
        destination = self.output_var.get().strip().strip('"')
        if not source or not destination:
            messagebox.showwarning("Caminho ausente", "Preencha os campos Input e Output.")
            return
        try:
            mode = self.export_mode.get()
            selected = int(self.line_var.get().split()[0]) - 1
            output, color_count, info = convert_file(source, destination, self.byte_order.get(), selected, mode)
            self.status.config(text=f"Concluído: {info['total_lines']} linha(s); {color_count} cores exportadas para {output}")
            messagebox.showinfo("Conversão concluída", f"{info['colors']} cores detectadas em {info['total_lines']} linha(s).\n"
                                f"{color_count} cores exportadas.\n\n{output}")
        except Exception as exc:
            self.status.config(text="Falha na conversão.")
            messagebox.showerror("Falha na conversão", str(exc))


def main():
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        details = traceback.format_exc()
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startup_error.log")
        try:
            with open(log_path, "w", encoding="utf-8") as log:
                log.write(details)
        except OSError:
            pass
        print(details, file=sys.stderr)
        try:
            messagebox.showerror("cram2binxel_MD — startup error", details + f"\n\nLog: {log_path}")
        except Exception:
            pass
        raise
