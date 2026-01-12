from __future__ import annotations

import random
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, font as tkfont

WORDS_FILE = Path(__file__).with_name("words.txt")
WORDS_USED_FILE = Path(__file__).with_name("words_used.txt")


class WerewolfGameApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("文字狼人杀")

        self.words = self.load_words()
        self.player_count: int | None = None
        self.current_player_index = 0
        self.undercover_index = 0
        self.player_words: list[str] = []
        self.current_pair: tuple[str, str] | None = None
        self.player_phase: str = "intro"

        self.base_width = 520
        self.base_height = 420
        self.min_scale = 0.8
        self.max_scale = 1.8
        self.current_scale = 1.0

        self.frame = tk.Frame(root, padx=30, pady=20)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.fonts: dict[str, tkfont.Font] = {}
        self.base_font_sizes: dict[str, int] = {}
        self.setup_fonts()

        self.player_entry: tk.Entry | None = None

        self.root.bind("<Configure>", self.handle_resize)

        self.create_start_screen()

    def setup_fonts(self) -> None:
        font_specs: dict[str, tuple[int, str]] = {
            "title": (18, "bold"),
            "body": (14, "normal"),
            "button": (14, "bold"),
            "player_heading": (16, "bold"),
            "word": (26, "bold"),
            "small": (12, "normal"),
        }
        for name, (size, weight) in font_specs.items():
            self.fonts[name] = tkfont.Font(family="Arial", size=size, weight=weight)
            self.base_font_sizes[name] = size

    def handle_resize(self, event: tk.Event) -> None:
        if event.width <= 0 or event.height <= 0:
            return
        scale_w = event.width / self.base_width
        scale_h = event.height / self.base_height
        target_scale = max(self.min_scale, min(self.max_scale, min(scale_w, scale_h)))
        if abs(target_scale - self.current_scale) < 0.02:
            return
        self.current_scale = target_scale
        for name, base_size in self.base_font_sizes.items():
            new_size = max(10, int(base_size * self.current_scale))
            self.fonts[name].configure(size=new_size)
        pad_x = int(30 * self.current_scale)
        pad_y = int(20 * self.current_scale)
        self.frame.configure(padx=pad_x, pady=pad_y)

    def load_words(self) -> list[tuple[str, str]]:
        if not WORDS_FILE.exists():
            messagebox.showerror("错误", f"找不到词库文件: {WORDS_FILE}")
            sys.exit(1)

        pairs: list[tuple[str, str]] = []
        for raw_line in WORDS_FILE.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split(",") if part.strip()]
            if len(parts) != 2:
                continue
            pairs.append((parts[0], parts[1]))

        if not pairs:
            messagebox.showerror("错误", "词库文件没有有效的词条")
            sys.exit(1)
        return pairs

    def clear_frame(self) -> None:
        for widget in self.frame.winfo_children():
            widget.destroy()

    def create_start_screen(self) -> None:
        self.clear_frame()
        tk.Label(self.frame, text="文字狼人杀", font=self.fonts["title"], anchor=tk.CENTER).pack(
            pady=(0, 20), fill=tk.X
        )
        tk.Label(
            self.frame,
            text="请输入参与玩家人数 (>=2)：",
            font=self.fonts["body"],
            anchor=tk.CENTER,
        ).pack(fill=tk.X)

        self.player_entry = tk.Entry(self.frame, justify="center", font=self.fonts["body"])
        self.player_entry.pack(pady=10, fill=tk.X, padx=40)
        self.player_entry.insert(0, "4")

        tk.Button(
            self.frame,
            text="开始游戏",
            command=self.handle_start,
            font=self.fonts["button"],
            width=14,
        ).pack(pady=5)

    def handle_start(self) -> None:
        if not self.player_entry:
            return
        raw_value = self.player_entry.get()
        try:
            count = int(raw_value)
        except ValueError:
            messagebox.showerror("错误", "请输入正确的数字")
            return

        if count < 2:
            messagebox.showerror("错误", "玩家人数必须大于等于2")
            return

        self.player_count = count
        self.start_round()

    def start_round(self) -> None:
        if not self.player_count:
            return
        if not self.words:
            messagebox.showinfo("提示", "词库已使用完，请更新 words.txt 或从 words_used.txt 移回词条。")
            return
        self.current_player_index = 0
        self.player_phase = "intro"
        selected_pair = random.choice(self.words)
        self.mark_word_used(selected_pair)
        majority_word, minority_word = selected_pair
        if random.choice((True, False)):
            majority_word, minority_word = minority_word, majority_word
        self.current_pair = (majority_word, minority_word)
        self.undercover_index = random.randrange(self.player_count)
        self.player_words = [majority_word for _ in range(self.player_count)]
        self.player_words[self.undercover_index] = minority_word
        self.show_player_screen()

    def mark_word_used(self, pair: tuple[str, str]) -> None:
        sanitized_line = ",".join(pair)
        try:
            raw_lines = WORDS_FILE.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            raw_lines = []
        new_lines: list[str] = []
        removed = False
        for raw in raw_lines:
            if not removed and raw.strip() == sanitized_line:
                removed = True
                continue
            new_lines.append(raw)
        WORDS_FILE.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        with WORDS_USED_FILE.open("a", encoding="utf-8") as used_file:
            used_file.write(sanitized_line + "\n")
        try:
            self.words.remove(pair)
        except ValueError:
            pass

    def show_player_screen(self) -> None:
        if self.player_count is None:
            return
        if self.current_player_index >= self.player_count:
            self.show_reveal_screen()
            return
        if self.player_phase == "intro":
            self.show_player_intro_screen()
        else:
            self.show_player_word_screen()

    def show_player_intro_screen(self) -> None:
        player_number = self.current_player_index + 1
        self.clear_frame()
        tk.Label(
            self.frame,
            text=f"玩家 {player_number}",
            font=self.fonts["player_heading"],
            anchor=tk.CENTER,
        ).pack(pady=(0, 20), fill=tk.X)
        tk.Label(
            self.frame,
            text=f"你是第 {player_number} 个玩家",
            font=self.fonts["body"],
            anchor=tk.CENTER,
        ).pack(fill=tk.X)
        tk.Label(
            self.frame,
            text="请点击下一步查看你的词",
            font=self.fonts["body"],
            anchor=tk.CENTER,
        ).pack(pady=20, fill=tk.X)
        tk.Button(
            self.frame,
            text="下一步",
            command=self.handle_intro_next,
            font=self.fonts["button"],
            width=14,
        ).pack(pady=15)

    def handle_intro_next(self) -> None:
        self.player_phase = "word"
        self.show_player_screen()

    def show_player_word_screen(self) -> None:
        player_number = self.current_player_index + 1
        word = self.player_words[self.current_player_index]
        self.clear_frame()
        tk.Label(
            self.frame,
            text=f"玩家 {player_number}",
            font=self.fonts["player_heading"],
            anchor=tk.CENTER,
        ).pack(pady=(0, 20), fill=tk.X)
        tk.Label(
            self.frame,
            text="你的词是：",
            font=self.fonts["body"],
            anchor=tk.CENTER,
        ).pack(fill=tk.X)
        tk.Label(
            self.frame,
            text=word,
            font=self.fonts["word"],
            fg="darkblue",
            anchor=tk.CENTER,
        ).pack(pady=10, fill=tk.BOTH, expand=True)

        button_text = "下一位" if player_number < self.player_count else "查看结果"
        tk.Button(
            self.frame,
            text=button_text,
            command=self.handle_word_next,
            font=self.fonts["button"],
            width=14,
        ).pack(pady=15)

    def handle_word_next(self) -> None:
        self.current_player_index += 1
        self.player_phase = "intro"
        self.show_player_screen()

    def show_reveal_screen(self) -> None:
        if self.player_count is None:
            return

        self.clear_frame()
        tk.Label(self.frame, text="结果公布", font=self.fonts["title"], anchor=tk.CENTER).pack(
            pady=(0, 20), fill=tk.X
        )
        tk.Label(
            self.frame,
            text=f"卧底是第 {self.undercover_index + 1} 个玩家",
            font=self.fonts["body"],
            anchor=tk.CENTER,
        ).pack(pady=5, fill=tk.X)

        if self.current_pair:
            tk.Label(
                self.frame,
                text=f"多数派词：{self.current_pair[0]}    卧底词：{self.current_pair[1]}",
                font=self.fonts["body"],
            ).pack(pady=5, fill=tk.X)

        players_text = "\n".join(
            f"玩家 {idx + 1}: {word}" for idx, word in enumerate(self.player_words)
        )
        tk.Label(
            self.frame,
            text=players_text,
            justify="left",
            font=self.fonts["body"],
            anchor=tk.NW,
        ).pack(pady=15, fill=tk.BOTH, expand=True)

        tk.Button(
            self.frame,
            text="下一局游戏",
            command=self.start_round,
            font=self.fonts["button"],
            width=14,
        ).pack(pady=5)
        tk.Button(
            self.frame,
            text="重新设定人数",
            command=self.create_start_screen,
            font=self.fonts["button"],
            width=14,
        ).pack(pady=5)


def main() -> None:
    root = tk.Tk()
    app = WerewolfGameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
