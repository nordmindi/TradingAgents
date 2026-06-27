import os
import sys
import re
from datetime import datetime
from fpdf import FPDF

class VeinReportPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        # DESIGN SYSTEM: VEIN AI WEB PALETTE
        self.colors = {
            'bg': (255, 255, 255),
            'surface': (250, 251, 253),
            'border': (230, 235, 245),
            'text_main': (17, 24, 39),      # Deep Navy/Black
            'text_muted': (107, 114, 128),  # Slate
            'accent': (0, 110, 255),        # Vein Azure
            'bull': (16, 185, 129),         # Emerald
            'bear': (225, 29, 72),          # Rose
            'warn': (245, 158, 11),         # Amber
            'white': (255, 255, 255)
        }
        self.l_margin_val = 15
        self.r_margin_val = 15
        self.set_margins(self.l_margin_val, 20, self.r_margin_val)
        self.content_width = 210 - self.l_margin_val - self.r_margin_val

    def header(self):
        if self.page_no() == 1: return
        # WEB STYLE HEADER BAR
        self.set_fill_color(*self.colors['accent'])
        self.rect(0, 0, self.w, 32, 'F')
        
        self.set_xy(self.l_margin_val, 10)
        self.set_text_color(*self.colors['white'])
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 8, 'VEIN AI // SUPPLY CHAIN INTELLIGENCE', ln=True)
        
        self.set_font('courier', 'B', 8)
        self.set_x(self.l_margin_val)
        self.cell(0, 4, 'FRAMEWORK_VERSION: 2.1.0 // STREAM: ENCRYPTED_DATA', ln=False)
        
        self.set_xy(self.w - 45, 12)
        self.set_font('helvetica', 'B', 10)
        self.cell(30, 10, f'REPORT PAGE {self.page_no()}', align='R')
        self.set_y(40)

    def footer(self):
        if self.page_no() == 1: return
        self.set_y(-15)
        self.set_font('courier', 'B', 8)
        self.set_text_color(*self.colors['text_muted'])
        self.set_draw_color(*self.colors['border'])
        self.line(self.l_margin_val, self.get_y(), self.w - self.r_margin_val, self.get_y())
        self.cell(self.content_width, 10, f'AUDIT_TRAIL_ID: {datetime.now().strftime("%Y%m%d%H%M%S")} | CONFIDENTIAL', align='C')

    def add_title_page(self, ticker, date_str):
        self.add_page()
        self.set_fill_color(*self.colors['accent'])
        self.rect(0, 0, self.w, 15, 'F')
        self.rect(0, self.h - 15, self.w, 15, 'F')
        
        self.set_y(100)
        self.set_font('helvetica', 'B', 36)
        self.set_text_color(*self.colors['text_main'])
        self.multi_cell(self.content_width, 15, 'SUPPLY CHAIN\nINTELLIGENCE', align='C')
        
        self.ln(10)
        self.set_font('courier', 'B', 22)
        self.set_text_color(*self.colors['accent'])
        self.cell(self.content_width, 20, f'TICKER: {ticker}', ln=True, align='C')
        
        self.set_y(220)
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(*self.colors['text_muted'])
        self.cell(self.content_width, 8, f'GENERATED ON {date_str.upper()}', ln=True, align='C')
        self.set_font('courier', '', 9)
        self.cell(self.content_width, 5, 'BY VEIN AI AUTONOMOUS FRAMEWORK', ln=True, align='C')

class MarkdownPDFGenerator:
    def __init__(self, ticker="UNKNOWN", date_str=""):
        self.pdf = VeinReportPDF()
        self.pdf.set_auto_page_break(auto=True, margin=25)
        self.pdf.add_title_page(ticker, date_str)
        self.colors = self.pdf.colors

    def _clean_line(self, text):
        if not text: return ""
        text = text.replace('↑', '+').replace('↓', '-').replace('→', '=')
        text = "".join(c for c in text if ord(c) < 256)
        # Collapse multiple spaces to prevent margin overflow
        text = re.sub(r'\s{3,}', ' ', text)
        return text.strip()

    def _get_status_style(self, text):
        t = text.upper()
        if any(w in t for w in ["BUY", "BULLISH", "OVERWEIGHT", "POSITIVE", "KÖP"]):
            return self.colors['bull'], " BULLISH "
        if any(w in t for w in ["SELL", "BEARISH", "NEGATIVE", "RISK", "UNDERWEIGHT", "SÄLJ"]):
            return self.colors['bear'], " BEARISH "
        return self.colors['warn'], " NEUTRAL "

    def draw_badge(self, text):
        color, label = self._get_status_style(text)
        self.pdf.set_fill_color(*color)
        self.pdf.set_text_color(*self.colors['white'])
        self.pdf.set_font('helvetica', 'B', 9)
        w = self.pdf.get_string_width(label) + 4
        self.pdf.cell(w, 6, label, fill=True, align='C')
        self.pdf.set_text_color(*self.colors['text_main'])

    def add_highlights_page(self, md_text):
        # Data extraction logic
        metrics = {"Recommendation": "N/A", "Action": "N/A", "Target": "N/A", "Stop": "N/A"}
        for line in md_text.split('\n'):
            if "Recommendation:" in line or "Rekommendation:" in line: metrics["Recommendation"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Action:" in line or "Åtgärd:" in line: metrics["Action"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Target Price:" in line or "Målkurs:" in line: metrics["Target"] = line.split(":", 1)[1].strip().replace("**", "")

        self.pdf.add_page()
        self.pdf.set_font('helvetica', 'B', 22)
        self.pdf.set_text_color(*self.colors['text_main'])
        self.pdf.cell(self.pdf.content_width, 15, "EXECUTIVE DASHBOARD", ln=True)
        self.pdf.ln(5)
        
        # Grid Layout
        start_y = self.pdf.get_y()
        card_w = (self.pdf.content_width / 2) - 4
        
        for i, (label, val) in enumerate(metrics.items()):
            x = self.pdf.l_margin_val if i % 2 == 0 else (self.pdf.l_margin_val + card_w + 8)
            y = start_y + (i // 2) * 35
            
            self.pdf.set_fill_color(*self.colors['surface'])
            self.pdf.rect(x, y, card_w, 30, 'F')
            self.pdf.set_draw_color(*self.colors['border'])
            self.pdf.rect(x, y, card_w, 30, 'D')
            
            self.pdf.set_xy(x + 5, y + 5)
            self.pdf.set_font('courier', 'B', 8)
            self.pdf.set_text_color(*self.colors['text_muted'])
            self.pdf.cell(0, 5, f"DATA_POINT::{label.upper()}", ln=True)
            
            self.pdf.set_xy(x + 5, y + 15)
            self.pdf.set_font('helvetica', 'B', 12)
            self.pdf.set_text_color(*self.colors['text_main'])
            self.pdf.multi_cell(card_w - 10, 6, self._clean_line(val))
            
        self.pdf.set_y(start_y + 75)

    def add_markdown_content(self, md_text):
        lines = md_text.split('\n')
        in_table = False
        table_rows = []
        
        for line in lines:
            raw_line = line.strip()
            line = self._clean_line(raw_line)
            
            if not line or line == '---':
                if in_table: self._render_table(table_rows); table_rows = []; in_table = False
                self.pdf.ln(4)
                continue

            if '|' in line and '---' in line:
                in_table = True; continue

            if '|' in line:
                in_table = True
                table_rows.append([p.strip() for p in line.split('|') if p.strip()])
                continue
            elif in_table:
                self._render_table(table_rows); table_rows = []; in_table = False

            # SECTION MODULES (Mimicking web tabs)
            self.pdf.set_x(self.pdf.l_margin_val)
            if raw_line.startswith('## '):
                self.pdf.ln(6)
                self.pdf.set_fill_color(*self.colors['surface'])
                self.pdf.rect(self.pdf.l_margin_val, self.pdf.get_y(), self.pdf.content_width, 12, 'F')
                self.pdf.set_xy(self.pdf.l_margin_val + 4, self.pdf.get_y() + 2)
                self.pdf.set_font('helvetica', 'B', 13)
                self.pdf.set_text_color(*self.colors['accent'])
                self.pdf.cell(0, 8, line[3:].upper())
                self.pdf.ln(12)
            
            elif raw_line.startswith('### '):
                self.pdf.set_font('helvetica', 'B', 11)
                self.pdf.set_text_color(*self.colors['text_main'])
                self.pdf.multi_cell(self.pdf.content_width, 8, line[4:])
            
            elif "Action:" in raw_line or "Recommendation:" in raw_line:
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.write(6, f"{line.split(':')[0]}: ")
                self.draw_badge(line.split(':')[1])
                self.pdf.ln(8)
            
            elif raw_line.startswith('- ') or raw_line.startswith('* '):
                self.pdf.set_x(self.pdf.l_margin_val + 5)
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.set_text_color(*self.colors['accent'])
                self.pdf.cell(5, 6, ">")
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text_main'])
                self.pdf.multi_cell(self.pdf.content_width - 10, 6, line[2:])
            
            else:
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text_main'])
                self.pdf.multi_cell(self.pdf.content_width, 6, line.replace("**", ""))

        if in_table: self._render_table(table_rows)

    def _render_table(self, rows):
        if not rows: return
        self.pdf.set_x(self.pdf.l_margin_val)
        with self.pdf.table(width=self.pdf.content_width, line_height=8, 
                            cell_fill_color=self.colors['surface'], cell_fill_mode="ROWS") as table:
            for i, row in enumerate(rows):
                r = table.row()
                self.pdf.set_font("helvetica", "B" if i == 0 else "", 9)
                for cell in row:
                    r.cell(self._clean_line(cell))
        self.pdf.ln(4)

    def save(self, output_path):
        self.pdf.output(output_path)
        print(f"REPORT_SYNC_COMPLETE: {output_path}")

# (Standard execution block stays same)
