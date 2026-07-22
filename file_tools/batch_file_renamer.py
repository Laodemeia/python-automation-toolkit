from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import uuid


INVALID_CHARACTERS = '<>:"/\\|?*'


class BatchFileRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch File Renamer")
        self.root.geometry("850x560")
        self.root.minsize(700, 450)

        self.folder = None
        self.preview_items = []

        self.folder_var = tk.StringVar(value="No folder selected")
        self.prefix_var = tk.StringVar(value="document")
        self.start_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="Select a folder to begin.")

        self.create_interface()

    def create_interface(self):
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Batch File Renamer",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            container,
            text="Rename multiple files safely with automatic numbering.",
        ).pack(anchor="w", pady=(2, 18))

        folder_frame = ttk.Frame(container)
        folder_frame.pack(fill="x")

        ttk.Entry(
            folder_frame,
            textvariable=self.folder_var,
            state="readonly",
        ).pack(side="left", fill="x", expand=True)

        ttk.Button(
            folder_frame,
            text="Select Folder",
            command=self.select_folder,
        ).pack(side="left", padx=(8, 0))

        settings = ttk.LabelFrame(container, text="Rename Settings", padding=12)
        settings.pack(fill="x", pady=15)

        ttk.Label(settings, text="File prefix:").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Entry(settings, textvariable=self.prefix_var, width=30).grid(
            row=0, column=1, sticky="ew"
        )

        ttk.Label(settings, text="Starting number:").grid(
            row=0, column=2, sticky="w", padx=(20, 8)
        )
        ttk.Entry(settings, textvariable=self.start_var, width=10).grid(
            row=0, column=3, sticky="ew"
        )

        settings.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(0, 12))

        ttk.Button(
            button_frame,
            text="Preview Changes",
            command=self.generate_preview,
        ).pack(side="left")

        ttk.Button(
            button_frame,
            text="Rename Files",
            command=self.rename_files,
        ).pack(side="left", padx=8)

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_preview,
        ).pack(side="left")

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)

        self.table = ttk.Treeview(
            table_frame,
            columns=("current", "new"),
            show="headings",
        )
        self.table.heading("current", text="Current Name")
        self.table.heading("new", text="New Name")
        self.table.column("current", width=350)
        self.table.column("new", width=350)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview,
        )
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(
            container,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=6,
        ).pack(fill="x", pady=(12, 0))

    def select_folder(self):
        selected_folder = filedialog.askdirectory(title="Select a folder")

        if not selected_folder:
            return

        self.folder = Path(selected_folder)
        self.folder_var.set(str(self.folder))
        self.clear_preview()
        self.status_var.set("Folder selected. Click Preview Changes.")

    def validate_settings(self):
        if self.folder is None:
            messagebox.showwarning("Missing Folder", "Please select a folder.")
            return None

        prefix = self.prefix_var.get().strip()

        if not prefix:
            messagebox.showwarning("Invalid Prefix", "Please enter a file prefix.")
            return None

        if any(character in prefix for character in INVALID_CHARACTERS):
            messagebox.showwarning(
                "Invalid Prefix",
                "The prefix contains characters that cannot be used in file names.",
            )
            return None

        try:
            start_number = int(self.start_var.get())
        except ValueError:
            messagebox.showwarning(
                "Invalid Number",
                "The starting number must be a whole number.",
            )
            return None

        if start_number < 0:
            messagebox.showwarning(
                "Invalid Number",
                "The starting number cannot be negative.",
            )
            return None

        return prefix, start_number

    def get_files(self):
        current_script = Path(__file__).resolve()

        return sorted(
            [
                file
                for file in self.folder.iterdir()
                if file.is_file() and file.resolve() != current_script
            ],
            key=lambda file: file.name.lower(),
        )

    def generate_preview(self):
        settings = self.validate_settings()

        if settings is None:
            return

        prefix, start_number = settings
        files = self.get_files()

        self.clear_preview()

        if not files:
            self.status_var.set("No files were found in the selected folder.")
            return

        last_number = start_number + len(files) - 1
        number_width = max(3, len(str(last_number)))
        source_paths = set(files)

        for index, source in enumerate(files, start=start_number):
            new_name = f"{prefix}_{index:0{number_width}d}{source.suffix}"
            target = source.with_name(new_name)

            if target.exists() and target not in source_paths:
                messagebox.showerror(
                    "Name Conflict",
                    f"A file named '{new_name}' already exists.",
                )
                self.clear_preview()
                return

            self.preview_items.append((source, target))
            self.table.insert("", "end", values=(source.name, target.name))

        self.status_var.set(
            f"{len(self.preview_items)} file(s) ready to be renamed."
        )

    def rename_files(self):
        if not self.preview_items:
            self.generate_preview()

        if not self.preview_items:
            return

        confirmed = messagebox.askyesno(
            "Confirm Rename",
            f"Rename {len(self.preview_items)} file(s)?",
        )

        if not confirmed:
            return

        temporary_files = []

        try:
            # Temporary names prevent conflicts during the rename operation.
            for source, target in self.preview_items:
                temporary_path = source.with_name(
                    f".rename_temp_{uuid.uuid4().hex}{source.suffix}"
                )
                source.rename(temporary_path)
                temporary_files.append((temporary_path, target))

            for temporary_path, target in temporary_files:
                temporary_path.rename(target)

        except OSError as error:
            messagebox.showerror(
                "Rename Error",
                f"The files could not be renamed:\n\n{error}",
            )
            return

        renamed_count = len(self.preview_items)
        self.clear_preview()
        self.status_var.set(f"Successfully renamed {renamed_count} file(s).")

        messagebox.showinfo(
            "Completed",
            f"{renamed_count} file(s) renamed successfully.",
        )

    def clear_preview(self):
        self.preview_items = []

        for item in self.table.get_children():
            self.table.delete(item)

        self.status_var.set("Preview cleared.")


def main():
    root = tk.Tk()
    BatchFileRenamer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
