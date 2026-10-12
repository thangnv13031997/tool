"""Horror Studio - desktop app (Tkinter).

Tab 1  Xuất video           : chọn kịch bản, xem trước từng cảnh, xuất MP4 + Shorts + 3 thumbnail + nội dung YouTube
Tab 2  Viết kịch bản AI     : viết kịch bản bằng Claude API, hoặc copy prompt để dán vào Claude chat
Tab 3  Tiêu đề & Thumbnail  : chấm điểm tiêu đề, xem 3 thumbnail trước khi xuất
Tab 4  Âm thanh             : nghe thử nhạc / âm nền / hiệu ứng, mở thư viện để thêm file của bạn
"""
import glob
import json
import multiprocessing
import os
import queue
import subprocess
import sys
import threading
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import tkinter as tk                              # noqa: E402
from tkinter import ttk, filedialog, messagebox   # noqa: E402

CFG_PATH = os.path.join(ROOT, 'config.json')
CFG_EXAMPLE = os.path.join(ROOT, 'config.example.json')
SCRIPTS = os.path.join(ROOT, 'scripts')
OUTPUT = os.path.join(ROOT, 'output')
NOTES = os.path.join(ROOT, 'notes', 'IMPROVEMENTS.md')
LOGS = os.path.join(ROOT, 'logs')
LIB = os.path.join(ROOT, 'library')

BG = '#121417'
PANEL = '#1B1F26'
FIELD = '#232832'
TEXT = '#E8E6E0'
MUTED = '#8A909A'
RED = '#C8102E'
YELLOW = '#E8B730'

GENRES = ['rules horror (danh sách luật lạ)', 'night shift (ca đêm)', 'stalker / bị theo dõi', 'home alone / người lạ trong nhà',
          'babysitting (trông trẻ)', 'camping / rừng đêm', 'road trip / lái xe đêm', 'creepy neighbor (hàng xóm)',
          'motel / Airbnb', 'mimic (thứ bắt chước giọng người)', 'doorbell camera / CCTV', 'Asian folklore (gia vị châu Á)']


def load_cfg():
    """config.example.json làm mặc định, config.json (riêng trên máy, không đưa lên git) ghi đè lên."""
    cfg = {}
    for p in (CFG_EXAMPLE, CFG_PATH):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    if not os.path.exists(CFG_PATH) and cfg:
        try:
            save_cfg(cfg)
        except Exception:
            pass
    return cfg


def save_cfg(cfg):
    with open(CFG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def open_path(p):
    try:
        if sys.platform == 'win32':
            os.startfile(p)  # noqa
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', p])
        else:
            subprocess.Popen(['xdg-open', p])
    except Exception as e:  # noqa
        messagebox.showerror('Không mở được', str(e))


def write_log(text):
    os.makedirs(LOGS, exist_ok=True)
    with open(os.path.join(LOGS, 'app.log'), 'a', encoding='utf-8') as f:
        f.write(text + '\n')


def play(path):
    if sys.platform == 'win32':
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        open_path(path)


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_cfg()
        self.q = queue.Queue()
        self.job = None
        self.preview_img = None
        self.thumb_imgs = []
        self.scene_count = 0
        self.last_out = None
        self.still_cache = {}
        self.ai_cancel = False
        for d in (SCRIPTS, OUTPUT, LOGS, os.path.dirname(NOTES), LIB):
            os.makedirs(d, exist_ok=True)
        root.title('Horror Studio - Bus 13: Night Route')
        root.geometry('1440x900')
        root.minsize(1100, 700)
        if sys.platform == 'win32':
            try:
                root.state('zoomed')
            except Exception:
                pass
        root.configure(bg=BG)
        ico = os.path.join(ROOT, 'assets', 'icon.ico')
        if sys.platform == 'win32' and os.path.exists(ico):
            try:
                root.iconbitmap(ico)
            except Exception:
                pass
        try:
            import script_io
            os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
            with open(os.path.join(ROOT, 'docs', 'library.json'), 'w', encoding='utf-8') as f:
                json.dump(script_io.library(), f, indent=1)
        except Exception:
            pass
        self._style()
        self._build()
        self.refresh_scripts()
        self.root.after(120, self._poll)

    # ------------------------------------------------------------------ style
    def _style(self):
        st = ttk.Style()
        try:
            st.theme_use('clam')
        except Exception:
            pass
        base = ('Segoe UI', 10)
        st.configure('.', font=base, background=BG, foreground=TEXT, fieldbackground=FIELD, bordercolor='#2C323C',
                     lightcolor=PANEL, darkcolor=PANEL, troughcolor=FIELD, selectbackground=RED, selectforeground='white')
        st.configure('TFrame', background=BG)
        st.configure('Panel.TFrame', background=PANEL)
        st.configure('TLabel', background=BG, foreground=TEXT)
        st.configure('Panel.TLabel', background=PANEL, foreground=TEXT)
        st.configure('Muted.TLabel', background=PANEL, foreground=MUTED)
        st.configure('H.TLabel', font=('Segoe UI Semibold', 12), background=BG, foreground=TEXT)
        st.configure('HP.TLabel', font=('Segoe UI Semibold', 12), background=PANEL, foreground=TEXT)
        st.configure('Score.TLabel', font=('Segoe UI Black', 20), background=PANEL, foreground=YELLOW)
        st.configure('TButton', padding=(10, 6), background='#2A303A', foreground=TEXT)
        st.map('TButton', background=[('active', '#353C48')])
        st.configure('Big.TButton', font=('Segoe UI Black', 13), padding=(14, 12), background=RED, foreground='white')
        st.map('Big.TButton', background=[('active', '#A50D25'), ('disabled', '#5A2A32')])
        st.configure('TCheckbutton', background=PANEL, foreground=TEXT)
        st.map('TCheckbutton', background=[('active', PANEL)])
        st.configure('TRadiobutton', background=PANEL, foreground=TEXT)
        st.map('TRadiobutton', background=[('active', PANEL)])
        st.configure('TNotebook', background=BG, borderwidth=0)
        st.configure('TNotebook.Tab', padding=(16, 8), background=PANEL, foreground=MUTED, font=('Segoe UI Semibold', 10))
        st.map('TNotebook.Tab', background=[('selected', RED)], foreground=[('selected', 'white')])
        st.configure('TCombobox', fieldbackground=FIELD, background=FIELD, foreground=TEXT, arrowcolor=TEXT)
        st.map('TCombobox', fieldbackground=[('readonly', FIELD)], foreground=[('readonly', TEXT)],
               selectbackground=[('readonly', FIELD)], selectforeground=[('readonly', TEXT)])
        st.configure('TSpinbox', fieldbackground=FIELD, background=FIELD, foreground=TEXT, arrowcolor=TEXT)
        st.configure('TEntry', fieldbackground=FIELD, foreground=TEXT)
        st.configure('Horizontal.TProgressbar', troughcolor=FIELD, background=RED, thickness=14)
        st.configure('Horizontal.TScale', background=PANEL, troughcolor=FIELD)
        self.root.option_add('*TCombobox*Listbox.background', FIELD)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT)

    def _text(self, parent, h=8, mono=False):
        return tk.Text(parent, height=h, font=('Consolas', 9) if mono else ('Segoe UI', 10), bg=FIELD, fg=TEXT,
                       insertbackground=TEXT, relief='flat', wrap='word', highlightthickness=0)

    # ------------------------------------------------------------------ layout
    def _build(self):
        top = tk.Frame(self.root, bg='#0B0C0E', height=60)
        top.pack(fill='x')
        tk.Label(top, text='  HORROR STUDIO', font=('Segoe UI Black', 18), bg='#0B0C0E', fg=RED).pack(side='left', pady=10)
        tk.Label(top, text='Bus 13: Night Route  ·  video kinh dị người que cho kênh nước ngoài  ', font=('Segoe UI', 10),
                 bg='#0B0C0E', fg=MUTED).pack(side='right')
        nb = ttk.Notebook(self.root)
        nb.pack(fill='both', expand=True, padx=10, pady=(8, 0))
        self.nb = nb
        t1, t2, t3, t4 = (ttk.Frame(nb) for _ in range(4))
        nb.add(t1, text='1. Xuất video')
        nb.add(t2, text='2. Viết kịch bản AI')
        nb.add(t3, text='3. Tiêu đề & Thumbnail')
        nb.add(t4, text='4. Âm thanh')
        self._tab_export(t1)
        self._tab_ai(t2)
        self._tab_titles(t3)
        self._tab_sound(t4)
        lf = ttk.Frame(self.root)
        lf.pack(fill='x', padx=10, pady=(6, 10))
        self.log_box = self._text(lf, 6, mono=True)
        self.log_box.pack(fill='x')
        self.log('Chào bạn! Chọn kịch bản, xem trước, rồi bấm XUẤT VIDEO.')
        self.log('Kokoro: ' + self.cfg.get('kokoro_python', '(chưa cấu hình)'))

    def _tab_export(self, tab):
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)
        left = ttk.Frame(tab, style='Panel.TFrame', padding=10)
        left.grid(row=0, column=0, sticky='nsw', padx=(0, 10), pady=8)
        ttk.Label(left, text='Kịch bản', style='HP.TLabel').pack(anchor='w')
        ttk.Label(left, text='File .json trong thư mục scripts', style='Muted.TLabel').pack(anchor='w', pady=(0, 6))
        self.lst = tk.Listbox(left, width=34, height=24, activestyle='none', font=('Segoe UI', 10), bg=FIELD, fg=TEXT,
                              selectbackground=RED, selectforeground='white', highlightthickness=0, relief='flat')
        self.lst.pack(fill='y', expand=True)
        self.lst.bind('<<ListboxSelect>>', lambda e: self.on_select())
        bf = ttk.Frame(left, style='Panel.TFrame')
        bf.pack(fill='x', pady=(8, 0))
        ttk.Button(bf, text='Làm mới', command=self.refresh_scripts).pack(side='left')
        ttk.Button(bf, text='Thêm file...', command=self.add_script).pack(side='left', padx=4)
        ttk.Button(bf, text='Mở thư mục', command=lambda: open_path(SCRIPTS)).pack(side='left')

        mid = ttk.Frame(tab)
        mid.grid(row=0, column=1, sticky='nsew', pady=8)
        mid.columnconfigure(0, weight=1)
        holder = tk.Frame(mid, bg='#000000', width=720, height=405)
        holder.grid(row=0, column=0, sticky='new')
        holder.bind('<Configure>', lambda e: holder.configure(height=int(e.width * 9 / 16)))
        holder.grid_propagate(False)
        holder.pack_propagate(False)
        self.holder = holder
        self.canvas = tk.Label(holder, bg='#000000', text='Chọn một kịch bản bên trái', font=('Segoe UI', 12), fg=MUTED)
        self.canvas.pack(fill='both', expand=True)
        sf = ttk.Frame(mid)
        sf.grid(row=1, column=0, sticky='ew', pady=6)
        sf.columnconfigure(1, weight=1)
        self.scene_lbl = ttk.Label(sf, text='Cảnh -/-', width=12)
        self.scene_lbl.grid(row=0, column=0)
        self.scale = ttk.Scale(sf, from_=1, to=1, orient='horizontal', command=lambda v: self._scene_moved())
        self.scale.grid(row=0, column=1, sticky='ew', padx=8)
        ttk.Button(sf, text='Kiểm tra kịch bản', command=self.check_script).grid(row=0, column=2)
        self.info = ttk.Label(mid, text='', justify='left')
        self.info.grid(row=2, column=0, sticky='w')
        self.scene_info = ttk.Label(mid, text='', justify='left', foreground=MUTED, wraplength=760)
        self.scene_info.grid(row=3, column=0, sticky='w', pady=(4, 0))

        right = ttk.Frame(tab, style='Panel.TFrame', padding=12)
        right.grid(row=0, column=2, sticky='nse', padx=(10, 0), pady=8)
        ttk.Label(right, text='Điểm giữ chân (ước lượng)', style='Muted.TLabel').pack(anchor='w')
        self.score_lbl = ttk.Label(right, text='--/100', style='Score.TLabel')
        self.score_lbl.pack(anchor='w', pady=(0, 8))
        import script_io
        ttk.Label(right, text='Giọng kể mặc định (nếu kịch bản không ghi)', style='Panel.TLabel').pack(anchor='w')
        vf = ttk.Frame(right, style='Panel.TFrame')
        vf.pack(fill='x')
        self.voice = ttk.Combobox(vf, values=script_io.ALL_VOICES, width=14, state='readonly')
        self.voice.set(self.cfg.get('narrator_voice', 'am_michael'))
        self.voice.pack(side='left')
        ttk.Button(vf, text='Nghe thử', command=self.test_voice).pack(side='left', padx=4)
        self.voice_fx = ttk.Combobox(right, values=['(giọng thường)', 'deep_reverb', 'whisper', 'creepy', 'phone', 'distant', 'demon'],
                                     width=18, state='readonly')
        self.voice_fx.set('(giọng thường)')
        self.voice_fx.pack(anchor='w', pady=(4, 0))
        ttk.Label(right, text='Tốc độ đọc chung', style='Panel.TLabel').pack(anchor='w', pady=(8, 0))
        self.speed = tk.DoubleVar(value=float(self.cfg.get('speed', 1.0)))
        ttk.Spinbox(right, from_=0.8, to=1.3, increment=0.05, textvariable=self.speed, width=8).pack(anchor='w')
        ttk.Label(right, text='Âm lượng nhạc nền', style='Panel.TLabel').pack(anchor='w', pady=(8, 0))
        self.music_vol = tk.DoubleVar(value=float(self.cfg.get('music_volume', 0.32)))
        ttk.Scale(right, from_=0.0, to=0.8, variable=self.music_vol, orient='horizontal', length=200).pack(anchor='w')
        self.music_on = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text='Nhạc + âm thanh nền + hiệu ứng', variable=self.music_on).pack(anchor='w', pady=(4, 0))
        self.shorts_on = tk.BooleanVar(value=bool(self.cfg.get('make_shorts', True)))
        ttk.Checkbutton(right, text='Cắt thêm bản Shorts dọc (<60s)', variable=self.shorts_on).pack(anchor='w')
        ttk.Label(right, text='Chế độ xuất', style='Panel.TLabel').pack(anchor='w', pady=(10, 0))
        self.mode = tk.StringVar(value='full')
        ttk.Radiobutton(right, text='Video đầy đủ', value='full', variable=self.mode).pack(anchor='w')
        ttk.Radiobutton(right, text='Xem thử 40 giây đầu', value='preview', variable=self.mode).pack(anchor='w')
        self.silent = tk.BooleanVar(value=False)
        ttk.Checkbutton(right, text='Thử nhanh không giọng (kiểm tra hình)', variable=self.silent).pack(anchor='w', pady=(4, 0))
        self.btn = ttk.Button(right, text='XUẤT VIDEO', style='Big.TButton', command=self.start)
        self.btn.pack(fill='x', pady=(14, 6))
        self.cancel_btn = ttk.Button(right, text='Hủy', command=self.cancel, state='disabled')
        self.cancel_btn.pack(fill='x')
        self.prog = ttk.Progressbar(right, length=250, mode='determinate', maximum=1000)
        self.prog.pack(fill='x', pady=(12, 2))
        self.status = ttk.Label(right, text='Sẵn sàng', style='Panel.TLabel', wraplength=260)
        self.status.pack(anchor='w')
        ttk.Separator(right).pack(fill='x', pady=10)
        ttk.Button(right, text='Mở thư mục video đã xuất', command=self.open_output).pack(fill='x')
        ttk.Button(right, text='Mở ghi chú cải thiện', command=self.open_notes).pack(fill='x', pady=4)
        ttk.Button(right, text='Mở config.json', command=lambda: open_path(CFG_PATH)).pack(fill='x')

    def _tab_ai(self, tab):
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)
        f = ttk.Frame(tab, style='Panel.TFrame', padding=12)
        f.grid(row=0, column=0, sticky='nsw', pady=8, padx=(0, 10))
        ttk.Label(f, text='Ý tưởng truyện (tiếng Việt hoặc tiếng Anh)', style='HP.TLabel').pack(anchor='w')
        self.idea = self._text(f, 6)
        self.idea.configure(width=46)
        self.idea.pack(fill='x', pady=(4, 8))
        self.idea.insert('1.0', 'Một cô gái nhận trông trẻ cho gia đình giàu, có danh sách luật kỳ lạ. Luật cuối: đừng tin nếu bố mẹ gọi về nói sắp về sớm.')
        ttk.Label(f, text='Thể loại', style='Panel.TLabel').pack(anchor='w')
        self.genre = ttk.Combobox(f, values=GENRES, width=44, state='readonly')
        self.genre.set(GENRES[0])
        self.genre.pack(anchor='w')
        row = ttk.Frame(f, style='Panel.TFrame')
        row.pack(fill='x', pady=(8, 0))
        ttk.Label(row, text='Số phút', style='Panel.TLabel').pack(side='left')
        self.minutes = tk.IntVar(value=8)
        ttk.Spinbox(row, from_=3, to=20, textvariable=self.minutes, width=5).pack(side='left', padx=(4, 16))
        ttk.Label(row, text='Nhân vật chính', style='Panel.TLabel').pack(side='left')
        self.gender = ttk.Combobox(row, values=['female', 'male'], width=8, state='readonly')
        self.gender.set('female')
        self.gender.pack(side='left', padx=4)
        ttk.Label(f, text='Yêu cầu thêm (không bắt buộc)', style='Panel.TLabel').pack(anchor='w', pady=(8, 0))
        self.extra = ttk.Entry(f, width=48)
        self.extra.pack(anchor='w')
        ttk.Separator(f).pack(fill='x', pady=10)
        ttk.Label(f, text='Cách 1 - Miễn phí: dán prompt vào Claude chat', style='HP.TLabel').pack(anchor='w')
        ttk.Label(f, text='Copy prompt, dán vào claude.ai, lưu JSON trả về vào thư mục scripts.', style='Muted.TLabel',
                  wraplength=360).pack(anchor='w')
        ttk.Button(f, text='Copy prompt + ý tưởng', command=self.copy_prompt).pack(anchor='w', pady=4)
        ttk.Label(f, text='Cách 2 - Tự động: Claude API (cần API key, tính phí)', style='HP.TLabel').pack(anchor='w', pady=(10, 0))
        ttk.Label(f, text='API key (lưu trong config.json trên máy bạn)', style='Muted.TLabel').pack(anchor='w')
        self.api_key = ttk.Entry(f, width=48, show='•')
        self.api_key.insert(0, self.cfg.get('anthropic_api_key', ''))
        self.api_key.pack(anchor='w')
        ttk.Label(f, text='Model', style='Muted.TLabel').pack(anchor='w', pady=(4, 0))
        self.model = ttk.Combobox(f, values=['claude-sonnet-5-5', 'claude-opus-5-5', 'claude-haiku-5-5'], width=24)
        self.model.set(self.cfg.get('claude_model', 'claude-sonnet-5-5'))
        self.model.pack(anchor='w')
        bf = ttk.Frame(f, style='Panel.TFrame')
        bf.pack(fill='x', pady=10)
        self.ai_btn = ttk.Button(bf, text='VIẾT KỊCH BẢN', style='Big.TButton', command=self.ai_write)
        self.ai_btn.pack(side='left')
        ttk.Button(bf, text='Dừng', command=self._ai_stop).pack(side='left', padx=6)
        self.ai_status = ttk.Label(f, text='', style='Muted.TLabel', wraplength=360)
        self.ai_status.pack(anchor='w')
        right = ttk.Frame(tab)
        right.grid(row=0, column=1, sticky='nsew', pady=8)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)
        ttk.Label(right, text='Kết quả (JSON). Có thể sửa trực tiếp rồi bấm Lưu.', style='H.TLabel').grid(row=0, column=0, sticky='w')
        self.ai_out = self._text(right, 30, mono=True)
        self.ai_out.grid(row=1, column=0, sticky='nsew', pady=4)
        bb = ttk.Frame(right)
        bb.grid(row=2, column=0, sticky='w')
        ttk.Button(bb, text='Lưu vào scripts', command=self.ai_save).pack(side='left')
        ttk.Button(bb, text='Dán JSON từ clipboard', command=self.ai_paste).pack(side='left', padx=6)

    def _tab_titles(self, tab):
        tab.columnconfigure(0, weight=1)
        top = ttk.Frame(tab, style='Panel.TFrame', padding=12)
        top.grid(row=0, column=0, sticky='ew', pady=8)
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text='Thử tiêu đề của bạn (chấm điểm tức thì)', style='HP.TLabel').grid(row=0, column=0, sticky='w')
        self.title_in = ttk.Entry(top, width=90)
        self.title_in.grid(row=1, column=0, sticky='ew', pady=4)
        self.title_in.bind('<KeyRelease>', lambda e: self.score_live())
        self.title_score = ttk.Label(top, text='', style='Panel.TLabel', justify='left')
        self.title_score.grid(row=2, column=0, sticky='w')
        ttk.Button(top, text='Tạo 3 thumbnail xem thử (kịch bản đang chọn)', command=self.preview_thumbs).grid(row=0, column=1, rowspan=2, padx=8)
        self.rank_box = self._text(tab, 9)
        self.rank_box.grid(row=1, column=0, sticky='ew')
        self.thumb_row = ttk.Frame(tab)
        self.thumb_row.grid(row=2, column=0, sticky='w', pady=8)
        self.thumb_lbls = []
        for i in range(3):
            lb = tk.Label(self.thumb_row, bg='#000000', fg=MUTED, text='ABC'[i], width=50, height=12)
            lb.pack(side='left', padx=4)
            self.thumb_lbls.append(lb)

    def _tab_sound(self, tab):
        import audio
        f = ttk.Frame(tab, style='Panel.TFrame', padding=12)
        f.pack(fill='both', expand=True, pady=8)
        ttk.Label(f, text='Nghe thử âm thanh tự tạo. Muốn dùng file của bạn: bỏ vào thư mục tương ứng (file của bạn luôn được ưu tiên).',
                  style='Panel.TLabel', wraplength=1100).pack(anchor='w')
        for kind, title, names, folder in (('music', 'Nhạc theo cảm xúc (mood)', sorted(audio.MUSIC), 'music'),
                                           ('amb', 'Âm thanh bối cảnh (ambience)', sorted(audio.AMB), 'ambience'),
                                           ('sfx', 'Hiệu ứng (sfx)', sorted(audio.SFX), 'sfx')):
            ttk.Label(f, text=title, style='HP.TLabel').pack(anchor='w', pady=(12, 2))
            row = ttk.Frame(f, style='Panel.TFrame')
            row.pack(fill='x')
            cb = ttk.Combobox(row, values=names, width=24, state='readonly')
            cb.set(names[0])
            cb.pack(side='left')
            ttk.Button(row, text='Nghe thử', command=lambda k=kind, c=cb: self.play_lib(k, c.get())).pack(side='left', padx=4)
            ttk.Button(row, text='Mở thư mục ' + folder, command=lambda d=folder: open_path(os.path.join(LIB, d))).pack(side='left')
        ttk.Label(f, text='Gợi ý nguồn nhạc an toàn: YouTube Studio > Audio Library, Pixabay Music (đọc giấy phép từng bài).\n'
                          'Nhạc theo mood: library/music/<mood>/file.mp3  ·  Âm nền: library/ambience/rain.mp3  ·  Hiệu ứng: library/sfx/knock.wav',
                  style='Muted.TLabel').pack(anchor='w', pady=(16, 0))

    # ------------------------------------------------------------------ helpers
    def log(self, text):
        self.log_box.insert('end', text + '\n')
        self.log_box.see('end')
        write_log(text)

    def refresh_scripts(self):
        self.files = sorted(glob.glob(os.path.join(SCRIPTS, '*.json')), key=os.path.getmtime, reverse=True)
        self.lst.delete(0, 'end')
        for f in self.files:
            self.lst.insert('end', os.path.basename(f))
        if self.files:
            self.lst.selection_set(0)
            self.on_select()

    def add_script(self):
        import shutil
        for p in filedialog.askopenfilenames(title='Chọn kịch bản', filetypes=[('Kịch bản JSON', '*.json')]):
            shutil.copy(p, SCRIPTS)
        self.refresh_scripts()

    def current(self):
        sel = self.lst.curselection()
        return self.files[sel[0]] if sel else None

    def on_select(self):
        path = self.current()
        if not path:
            return
        try:
            import render
            script, issues, score, rissues = render.prepare_preview(self.cfg, path)
            self.cur_script = script
            self.scene_count = len(script['scenes'])
            self.scale.configure(to=max(1, self.scene_count))
            self.scale.set(1)
            words = sum(len(l['tts_text'].split()) for s in script['scenes'] for l in s['lines'])
            est = script['total']
            self.info.configure(text=f'{script["title"]}\n{self.scene_count} cảnh | {words} từ | khoảng {int(est // 60)} phút {int(est % 60)} giây'
                                     f' | {len(script["cast"])} nhân vật | {len(issues) + len(rissues)} cảnh báo')
            self.score_lbl.configure(text=f'{score}/100', foreground=YELLOW if score >= 80 else RED)
            self.render_still(0)
            self.fill_titles(script)
        except Exception as e:  # noqa
            self.info.configure(text='Lỗi đọc kịch bản: ' + str(e))
            self.log('Lỗi đọc kịch bản: ' + str(e))
            write_log(traceback.format_exc())

    def _scene_moved(self):
        i = int(round(float(self.scale.get())))
        self.scene_lbl.configure(text=f'Cảnh {i}/{self.scene_count}')
        if getattr(self, '_still_after', None):
            self.root.after_cancel(self._still_after)
        self._still_after = self.root.after(160, lambda: self.render_still(i - 1))

    def render_still(self, idx):
        path = self.current()
        if not path:
            return
        self.scene_lbl.configure(text=f'Cảnh {idx + 1}/{self.scene_count}')
        try:
            sc = self.cur_script['scenes'][idx]
            txt = f'[{sc["purpose"] or "-"}] nền {sc["bg"]} · camera {sc["camera"]} · nhạc {sc["mood"]} · âm nền {sc["ambience"]}'
            if sc.get('events'):
                txt += ' · ' + ', '.join(e['kind'] for e in sc['events'])
            txt += '\n' + ' / '.join(f'{l["speaker"]}: {l["tts_text"]}' for l in sc['lines'])
            self.scene_info.configure(text=txt)
        except Exception:
            pass
        w = self.holder.winfo_width()
        w = 720 if w < 100 else max(480, min(1100, w))

        def work():
            try:
                import render
                img = render.still(self.cfg, path, idx, 0.65, w, self.still_cache)
                self.q.put(('still', img))
            except Exception as e:  # noqa
                self.q.put(('log', 'Lỗi xem trước: ' + str(e)))
                write_log(traceback.format_exc())
        threading.Thread(target=work, daemon=True).start()

    def check_script(self):
        path = self.current()
        if not path:
            return
        import render
        script, issues, score, rissues = render.prepare_preview(self.cfg, path)
        self.log(f'Kiểm tra: điểm giữ chân {score}/100')
        if not issues and not rissues:
            self.log('Kiểm tra: không thấy vấn đề nào.')
        for it in issues + rissues:
            self.log('Kiểm tra: ' + str(it))

    def test_voice(self):
        voice = self.voice.get()
        vfx = self.voice_fx.get()
        vfx = None if vfx.startswith('(') else vfx
        self.log(f'Đang tạo giọng thử {voice} {vfx or ""}...')

        def work():
            try:
                import tts
                v = tts.Voice(self.cfg, os.path.join(OUTPUT, '_tts_cache'), log=lambda m: self.q.put(('log', m)))
                text = 'Some buses don\'t appear on any schedule... Tonight\'s passenger still smells like rain.'
                p = tts.PITCH.get(tts.base_fx(vfx), 1.0)
                items = [{'text': s, 'voice': voice, 'speed': round(float(self.speed.get()) / p ** 0.5, 3)} for s in tts.segments(text)]
                v.synth(items)
                a = tts.build_line_audio({'vfx': vfx}, items)
                out = os.path.join(OUTPUT, '_tts_cache', '_voice_test.wav')
                tts.write_wav(out, a)
                self.q.put(('play', out))
            except Exception as e:  # noqa
                self.q.put(('error', 'Không tạo được giọng thử', str(e)))
        threading.Thread(target=work, daemon=True).start()

    def play_lib(self, kind, name):
        def work():
            try:
                import audio
                import render
                lib = audio.Library(render.ffmpeg_exe(self.cfg), log=lambda m: self.q.put(('log', m)))
                data = lib.get(kind, name)
                if data is None:
                    raise RuntimeError('Không có âm thanh này')
                out = os.path.join(OUTPUT, '_tts_cache', f'_play_{kind}_{name}.wav')
                os.makedirs(os.path.dirname(out), exist_ok=True)
                audio.write_wav(out, data[:audio.SR * 12])
                self.q.put(('play', out))
            except Exception as e:  # noqa
                self.q.put(('error', 'Không phát được', str(e)))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------ titles
    def fill_titles(self, script):
        import youtube
        import script_io
        try:
            best, text, ranked = youtube.build_text(script, [], script_io.Issue)
        except Exception as e:  # noqa
            self.rank_box.delete('1.0', 'end')
            self.rank_box.insert('1.0', 'Lỗi: ' + str(e))
            return
        self.rank_box.delete('1.0', 'end')
        self.rank_box.insert('1.0', 'Xếp hạng tiêu đề trong kịch bản đang chọn:\n')
        for s, t, n in ranked:
            self.rank_box.insert('end', f'{s:3d}  {t}\n')
            for x in n:
                self.rank_box.insert('end', f'       - {x}\n')

    def score_live(self):
        import youtube
        s, n = youtube.score_title(self.title_in.get())
        self.title_score.configure(text=f'Điểm: {s}/100   ' + ('  ·  '.join(n) if n else 'Tốt!'),
                                   foreground=YELLOW if s >= 80 else TEXT)

    def preview_thumbs(self):
        path = self.current()
        if not path:
            return
        self.log('Đang tạo 3 thumbnail xem thử...')

        def work():
            try:
                import render
                import youtube
                import script_io
                from engine import thumbnail
                script, *_ = render.prepare_preview(self.cfg, path)
                best, _, _ = youtube.build_text(script, [], script_io.Issue)
                yt = script.get('youtube') or {}
                th = yt.get('thumbnail') or {}
                variants = th.get('variants') or ([th] if th else [])
                while len(variants) < 3:
                    b = dict(variants[0]) if variants else {}
                    b['layout'] = ['face_threat', 'object', 'split'][len(variants)]
                    variants.append(b)
                imgs = [thumbnail.render(v, script['cast'], best) for v in variants[:3]]
                self.q.put(('thumbs', imgs))
            except Exception as e:  # noqa
                self.q.put(('log', 'Lỗi thumbnail: ' + str(e)))
                write_log(traceback.format_exc())
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------ AI
    def copy_prompt(self):
        try:
            import claude_api
            text = claude_api.system_prompt() + '\n\n---\n\n' + claude_api.user_prompt(
                self.idea.get('1.0', 'end').strip(), self.genre.get(), self.minutes.get(), self.gender.get(), self.extra.get())
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.ai_status.configure(text='Đã copy. Dán vào Claude chat, rồi copy JSON trả về và bấm "Dán JSON từ clipboard".')
        except Exception as e:  # noqa
            messagebox.showerror('Lỗi', str(e))

    def ai_write(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showinfo('Thiếu API key', 'Nhập Anthropic API key, hoặc dùng Cách 1 (copy prompt sang Claude chat).')
            return
        self.cfg['anthropic_api_key'] = key
        self.cfg['claude_model'] = self.model.get()
        save_cfg(self.cfg)
        self.ai_out.delete('1.0', 'end')
        self.ai_btn.configure(state='disabled')
        self.ai_cancel = False
        self.ai_status.configure(text='Claude đang viết... (2-5 phút cho video 8-10 phút)')
        idea, genre, mins, gender, extra = (self.idea.get('1.0', 'end').strip(), self.genre.get(), self.minutes.get(),
                                            self.gender.get(), self.extra.get())

        def work():
            try:
                import claude_api
                text = claude_api.write_script(key, idea, genre, mins, gender, self.model.get(), extra,
                                               on_text=lambda s: self.q.put(('ai_text', s)), cancelled=lambda: self.ai_cancel)
                self.q.put(('ai_done', text))
            except Exception as e:  # noqa
                self.q.put(('ai_fail', str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _ai_stop(self):
        self.ai_cancel = True

    def ai_paste(self):
        try:
            self.ai_out.delete('1.0', 'end')
            self.ai_out.insert('1.0', self.root.clipboard_get())
        except Exception:
            pass

    def ai_save(self):
        import claude_api
        import render
        try:
            data = claude_api.extract_json(self.ai_out.get('1.0', 'end'))
        except Exception as e:  # noqa
            messagebox.showerror('JSON lỗi', f'Không đọc được JSON: {e}\nKiểm tra lại hoặc nhờ Claude sửa.')
            return
        import re
        import datetime
        name = re.sub(r'[^A-Za-z0-9]+', '_', data.get('title', 'story')).strip('_')[:50]
        path = os.path.join(SCRIPTS, datetime.datetime.now().strftime('%Y%m%d_%H%M_') + name + '.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        self.log('Đã lưu kịch bản: ' + path)
        self.refresh_scripts()
        try:
            _, issues, score, rissues = render.prepare_preview(self.cfg, path)
            self.ai_status.configure(text=f'Đã lưu. Điểm giữ chân {score}/100, {len(issues) + len(rissues)} cảnh báo (xem log).')
            for it in issues + rissues:
                self.log('Kiểm tra: ' + str(it))
        except Exception as e:  # noqa
            self.ai_status.configure(text='Đã lưu nhưng kịch bản có lỗi: ' + str(e))
        self.nb.select(0)

    # ------------------------------------------------------------------ render
    def start(self):
        path = self.current()
        if not path:
            messagebox.showinfo('Chưa chọn', 'Hãy chọn một kịch bản trước.')
            return
        self.cfg['narrator_voice'] = self.voice.get()
        try:
            self.cfg['speed'] = round(float(self.speed.get()), 2)
        except Exception:
            pass
        self.cfg['music_volume'] = round(float(self.music_vol.get()), 2)
        self.cfg['make_shorts'] = bool(self.shorts_on.get())
        save_cfg(self.cfg)
        import render
        self.job = render.Job(dict(self.cfg), path, test_voice=self.silent.get(),
                              preview_secs=40 if self.mode.get() == 'preview' else None, music=self.music_on.get(),
                              shorts=self.shorts_on.get(), report=lambda st, f, txt: self.q.put(('prog', st, f, txt)),
                              log=lambda m: self.q.put(('log', m)))
        self.btn.configure(state='disabled')
        self.cancel_btn.configure(state='normal')
        self.prog['value'] = 0
        self.log(f'Bắt đầu xuất: {os.path.basename(path)}')

        def work():
            try:
                self.q.put(('done', self.job.run()))
            except Exception as e:  # noqa
                write_log(traceback.format_exc())
                self.q.put(('fail', str(e)))
        threading.Thread(target=work, daemon=True).start()

    def cancel(self):
        if self.job:
            self.job.cancel = True
            self.status.configure(text='Đang hủy...')

    def open_output(self):
        open_path(self.last_out if self.last_out and os.path.isdir(self.last_out) else OUTPUT)

    def open_notes(self):
        if not os.path.exists(NOTES):
            import notes
            with open(NOTES, 'w', encoding='utf-8') as f:
                f.write(notes.HEADER)
        open_path(NOTES)

    def _poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == 'still' and msg[1] is not None:
                    from PIL import ImageTk
                    self.preview_img = ImageTk.PhotoImage(msg[1])
                    self.canvas.configure(image=self.preview_img, text='')
                elif kind == 'thumbs':
                    from PIL import ImageTk
                    self.thumb_imgs = [ImageTk.PhotoImage(im.resize((416, 234))) for im in msg[1]]
                    for lb, im in zip(self.thumb_lbls, self.thumb_imgs):
                        lb.configure(image=im, text='', width=416, height=234)
                    self.log('Đã tạo 3 thumbnail xem thử (A, B, C).')
                elif kind == 'log':
                    self.log(msg[1])
                elif kind == 'prog':
                    _, st, f, txt = msg
                    weights = {'voice': (0, 0.2), 'frames': (0.2, 0.92), 'mux': (0.92, 0.95), 'extras': (0.95, 1.0), 'done': (1.0, 1.0)}
                    a, b = weights.get(st, (0, 1))
                    self.prog['value'] = int(1000 * (a + (b - a) * f))
                    self.status.configure(text=txt)
                elif kind == 'play':
                    self.log('Đang phát âm thanh.')
                    play(msg[1])
                elif kind == 'error':
                    messagebox.showerror(msg[1], msg[2])
                    self.log(msg[1] + ': ' + msg[2])
                elif kind == 'ai_text':
                    self.ai_out.insert('end', msg[1])
                    self.ai_out.see('end')
                elif kind == 'ai_done':
                    self.ai_btn.configure(state='normal')
                    self.ai_status.configure(text='Xong! Bấm "Lưu vào scripts" để kiểm tra và đưa vào danh sách.')
                elif kind == 'ai_fail':
                    self.ai_btn.configure(state='normal')
                    self.ai_status.configure(text='Lỗi: ' + msg[1][:300])
                    self.log('Claude API lỗi: ' + msg[1])
                elif kind == 'done':
                    self.last_out = msg[1]
                    self._finish()
                    self.prog['value'] = 1000
                    self.status.configure(text='Xong! Video, Shorts, thumbnail và nội dung YouTube đã sẵn sàng.')
                    self.log('Xong: ' + msg[1])
                    if getattr(self.job, 'issues', []):
                        self.log(f'Có {len(self.job.issues)} điểm cần cải thiện, đã ghi vào notes/IMPROVEMENTS.md')
                    if messagebox.askyesno('Xuất xong', 'Video đã xuất xong.\nMở thư mục chứa video?'):
                        open_path(msg[1])
                elif kind == 'fail':
                    self._finish()
                    self.status.configure(text='Lỗi: ' + msg[1][:200])
                    self.log('LỖI: ' + msg[1])
                    if 'hủy' not in msg[1]:
                        messagebox.showerror('Xuất video lỗi', msg[1][:1500] + '\n\nChi tiết: logs/app.log')
        except queue.Empty:
            pass
        self.root.after(120, self._poll)

    def _finish(self):
        self.btn.configure(state='normal')
        self.cancel_btn.configure(state='disabled')


def main():
    multiprocessing.freeze_support()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
