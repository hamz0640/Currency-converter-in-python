import customtkinter as ctk
import requests
import threading
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG          = "#0D0D0D"
CARD        = "#161616"
BORDER      = "#2A2A2A"
ACCENT      = "#C8A96E"
ACCENT_DIM  = "#8A7248"
TEXT_PRI    = "#F0EDE8"
TEXT_SEC    = "#888480"
GREEN       = "#4CAF82"
RED         = "#E05A5A"

FONT_DISPLAY = ("Georgia", 28, "bold")
FONT_LABEL   = ("Georgia", 11)
FONT_RESULT  = ("Georgia", 18, "bold")
FONT_SMALL   = ("Helvetica", 10)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(BASE_DIR, "assets", "currency-conversion.ico")

CURRENCIES = [
    'AED','AFN','ALL','AMD','ANG','AOA','ARS','AUD','AWG','AZN',
    'BAM','BBD','BDT','BGN','BHD','BIF','BMD','BND','BOB','BRL',
    'BSD','BTN','BWP','BYN','BZD','CAD','CDF','CHF','CLP','CNY',
    'COP','CRC','CUP','CVE','CZK','DJF','DKK','DOP','DZD','EGP',
    'ERN','ETB','EUR','FJD','FKP','GBP','GEL','GHS','GIP','GMD',
    'GNF','GTQ','GYD','HKD','HNL','HTG','HUF','IDR','ILS','INR',
    'IQD','IRR','ISK','JMD','JOD','JPY','KES','KGS','KHR','KMF',
    'KRW','KWD','KYD','KZT','LAK','LBP','LKR','LRD','LSL','LYD',
    'MAD','MDL','MGA','MKD','MMK','MNT','MOP','MRU','MUR','MVR',
    'MWK','MXN','MYR','MZN','NAD','NGN','NIO','NOK','NPR','NZD',
    'OMR','PAB','PEN','PGK','PHP','PKR','PLN','PYG','QAR','RON',
    'RSD','RUB','RWF','SAR','SBD','SCR','SDG','SEK','SGD','SHP',
    'SLE','SOS','SRD','SSP','STN','SYP','SZL','THB','TJS','TMT',
    'TND','TOP','TRY','TTD','TWD','TZS','UAH','UGX','USD','UYU',
    'UZS','VES','VND','VUV','WST','XAF','XCD','XOF','XPF','YER',
    'ZAR','ZMW','ZWL',
]

CURRENCY_SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
    'INR': '₹', 'KRW': '₩', 'RUB': '₽', 'TRY': '₺', 'BRL': 'R$',
    'CHF': 'Fr', 'CAD': 'C$', 'AUD': 'A$', 'HKD': 'HK$', 'SGD': 'S$',
    'NOK': 'kr', 'SEK': 'kr', 'DKK': 'kr', 'MXN': 'MX$', 'ZAR': 'R',
}

load_dotenv()

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_symbol(code: str) -> str:
    return CURRENCY_SYMBOLS.get(code, code)


def format_number(n: float) -> str:
    if n >= 1_000_000:
        return f"{n:,.2f}"
    if n >= 1:
        return f"{n:,.4f}".rstrip('0').rstrip('.')
    return f"{n:.6f}".rstrip('0').rstrip('.')


# ── API ────────────────────────────────────────────────────────────────────────

def fetch_rate(base: str, target: str, callback):
    def _worker():
        try:
            api_key = os.getenv("EXCHANGE_API_KEY")
            r = requests.get(
                'https://open.er-api.com/v6/latest',
                params={'apikey': api_key, 'base': base},
                timeout=8,
            )
            data = r.json()
            if data.get('result') == 'success':
                rate = data['rates'].get(target)
                callback('ok', rate, data.get('time_last_update_utc', ''))
            else:
                callback('error', None, data.get('error-type', 'Unknown error'))
        except requests.exceptions.ConnectionError:
            callback('error', None, 'No internet connection')
        except Exception as e:
            callback('error', None, str(e))

    threading.Thread(target=_worker, daemon=True).start()


# ── App ────────────────────────────────────────────────────────────────────────

class CurrencyConverterApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Currency Converter")
        self.geometry("460x700")
        self.minsize(420, 640)
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self._last_rate: Optional[float] = None

        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print("Icon error:", e)

        self._build_ui()

    # ── UI Build ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer padding frame
        outer = ctk.CTkFrame(self, fg_color=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=28)

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(outer, fg_color=BG)
        hdr.pack(fill="x", pady=(0, 24))

        ctk.CTkLabel(
            hdr, text="Currency Converter", font=("Georgia", 26, "bold"),
            text_color=TEXT_PRI,
        ).pack(side="left")

        self.clock_label = ctk.CTkLabel(
            hdr, text="", font=FONT_SMALL, text_color=TEXT_SEC,
        )
        self.clock_label.pack(side="right", anchor="s", pady=(0, 4))
        self._tick_clock()

        # ── Divider ─────────────────────────────────────────────────────────────
        ctk.CTkFrame(outer, height=1, fg_color=BORDER).pack(fill="x", pady=(0, 24))

        # ── Amount card ─────────────────────────────────────────────────────────
        self._section_label(outer, "AMOUNT")
        amount_card = self._card(outer)

        self.amount_var = ctk.StringVar(value="1")
        self.amount_entry = ctk.CTkEntry(
            amount_card,
            textvariable=self.amount_var,
            font=("Georgia", 22),
            fg_color="transparent",
            border_width=0,
            text_color=TEXT_PRI,
            placeholder_text="0.00",
            placeholder_text_color=TEXT_SEC,
            height=44,
        )
        self.amount_entry.pack(fill="x", padx=16, pady=10)
        self.amount_var.trace_add("write", lambda *_: self._on_input_change())

        # ── Currency row ─────────────────────────────────────────────────────────
        cur_row = ctk.CTkFrame(outer, fg_color=BG)
        cur_row.pack(fill="x", pady=(16, 0))
        cur_row.columnconfigure(0, weight=1)
        cur_row.columnconfigure(1, weight=0)
        cur_row.columnconfigure(2, weight=1)

        # Base
        base_col = ctk.CTkFrame(cur_row, fg_color=BG)
        base_col.grid(row=0, column=0, sticky="ew")
        self._section_label(base_col, "FROM")
        base_card = self._card(base_col)
        self.base_cb = self._currency_combo(base_card, "USD")

        # Swap button
        swap_col = ctk.CTkFrame(cur_row, fg_color=BG)
        swap_col.grid(row=0, column=1, padx=10, pady=(22, 0))
        self.swap_btn = ctk.CTkButton(
            swap_col,
            text="⇄",
            width=40, height=40,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=ACCENT,
            font=("Helvetica", 18),
            border_width=1,
            border_color=BORDER,
            corner_radius=20,
            command=self._swap,
        )
        self.swap_btn.pack()

        # Target
        tgt_col = ctk.CTkFrame(cur_row, fg_color=BG)
        tgt_col.grid(row=0, column=2, sticky="ew")
        self._section_label(tgt_col, "TO")
        tgt_card = self._card(tgt_col)
        self.tgt_cb = self._currency_combo(tgt_card, "EUR")

        # Wire combo changes
        self.base_cb.configure(command=lambda _: self._on_input_change())
        self.tgt_cb.configure(command=lambda _: self._on_input_change())

        # ── Convert button ───────────────────────────────────────────────────────
        self.convert_btn = ctk.CTkButton(
            outer,
            text="CONVERT",
            height=52,
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            text_color="#0D0D0D",
            font=("Georgia", 14, "bold"),
            corner_radius=6,
            command=self._convert,
        )
        self.convert_btn.pack(fill="x", pady=(24, 0))

        # ── Result card ──────────────────────────────────────────────────────────
        ctk.CTkFrame(outer, height=1, fg_color=BORDER).pack(fill="x", pady=(28, 0))

        result_outer = ctk.CTkFrame(outer, fg_color=BG)
        result_outer.pack(fill="x", pady=(20, 0))

        self.result_label = ctk.CTkLabel(
            result_outer,
            text="—",
            font=FONT_RESULT,
            text_color=TEXT_PRI,
            wraplength=380,
            justify="center",
        )
        self.result_label.pack()

        self.rate_label = ctk.CTkLabel(
            result_outer,
            text="",
            font=FONT_SMALL,
            text_color=TEXT_SEC,
        )
        self.rate_label.pack(pady=(6, 0))

        self.status_label = ctk.CTkLabel(
            result_outer,
            text="",
            font=FONT_SMALL,
            text_color=TEXT_SEC,
        )
        self.status_label.pack(pady=(4, 0))

        # ── Quick amounts ────────────────────────────────────────────────────────
        ctk.CTkFrame(outer, height=1, fg_color=BORDER).pack(fill="x", pady=(24, 0))
        self._section_label(outer, "QUICK AMOUNTS")

        quick_row = ctk.CTkFrame(outer, fg_color=BG)
        quick_row.pack(fill="x", pady=(8, 0))
        for amt in [100, 500, 1000, 5000]:
            ctk.CTkButton(
                quick_row,
                text=str(amt),
                fg_color=CARD,
                hover_color=BORDER,
                text_color=TEXT_PRI,
                font=FONT_SMALL,
                border_width=1,
                border_color=BORDER,
                corner_radius=4,
                height=32,
                command=lambda a=amt: self._set_amount(a),
            ).pack(side="left", expand=True, fill="x", padx=3)

    # ── Widget helpers ─────────────────────────────────────────────────────────

    def _card(self, parent) -> ctk.CTkFrame:
        f = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_color=BORDER,
            border_width=1,
            corner_radius=6,
        )
        f.pack(fill="x", pady=(4, 0))
        return f

    def _section_label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Helvetica", 9),
            text_color=TEXT_SEC,
        ).pack(anchor="w", pady=(10, 0))

    def _currency_combo(self, parent, default: str) -> ctk.CTkComboBox:
        cb = ctk.CTkComboBox(
            parent,
            values=CURRENCIES,
            width=140,
            fg_color=CARD,
            border_color=CARD,
            button_color=CARD,
            button_hover_color=BORDER,
            dropdown_fg_color=CARD,
            dropdown_hover_color=BORDER,
            dropdown_text_color=TEXT_PRI,
            text_color=TEXT_PRI,
            font=("Georgia", 14, "bold"),
            state="readonly"
        )
        cb.set(default)
        cb.pack(padx=12, pady=10)
        return cb

    # ── Logic ──────────────────────────────────────────────────────────────────

    def _set_amount(self, value: int):
        self.amount_var.set(str(value))
        self._convert()

    def _swap(self):
        b, t = self.base_cb.get(), self.tgt_cb.get()
        self.base_cb.set(t)
        self.tgt_cb.set(b)
        self._convert()

    def _on_input_change(self):
        self.result_label.configure(text="—", text_color=TEXT_PRI)
        self.rate_label.configure(text="")

    def _convert(self):
        base = self.base_cb.get()
        target = self.tgt_cb.get()
        raw = self.amount_var.get().strip().replace(",", "")

        if not raw:
            self._show_error("Enter an amount")
            return
        try:
            amount = float(raw)
        except ValueError:
            self._show_error("Invalid number")
            return
        if amount < 0:
            self._show_error("Amount must be positive")
            return

        self.convert_btn.configure(text="…", state="disabled")
        self.status_label.configure(text="Fetching rate…", text_color=TEXT_SEC)

        def on_result(status, rate, meta):
            self.after(0, lambda: self._handle_result(status, rate, meta, amount, base, target))

        fetch_rate(base, target, on_result)

    def _handle_result(self, status, rate, meta, amount, base, target):
        self.convert_btn.configure(text="CONVERT", state="normal")
        if status == 'error':
            self._show_error(meta)
            return

        self._last_rate = rate
        converted = amount * rate

        self.result_label.configure(
            text=f"{format_number(amount)} {base}  =  {format_number(converted)} {target}",
            text_color=GREEN,
        )
        self.rate_label.configure(
            text=f"1 {base} = {format_number(rate)} {target}",
            text_color=ACCENT,
        )

        try:
            dt = datetime.strptime(meta, "%a, %d %b %Y %H:%M:%S +0000")
            self.status_label.configure(
                text=f"Rate updated {dt.strftime('%d %b %Y, %H:%M')} UTC",
                text_color=TEXT_SEC,
            )
        except Exception:
            self.status_label.configure(text="", text_color=TEXT_SEC)

    def _show_error(self, msg: str):
        self.result_label.configure(text=msg, text_color=RED)
        self.rate_label.configure(text="")
        self.status_label.configure(text="")

    def _tick_clock(self):
        now = datetime.utcnow().strftime("%H:%M:%S UTC")
        self.clock_label.configure(text=now)
        self.after(1000, self._tick_clock)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.mainloop()