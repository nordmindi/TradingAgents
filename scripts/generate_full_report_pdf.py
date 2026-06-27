import os
import sys
import re
from datetime import datetime
from fpdf import FPDF

class VeinReportPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        # BRAND PALETTE EXTRACTED FROM ASSETS
        self.colors = {
            'bg': (255, 255, 255),
            'navy': (28, 62, 116),        # From Logo "V/E"
            'lime': (154, 205, 50),       # From Logo "I/N"
            'gold': (255, 204, 102),      # From Analyst Icon BG
            'cream': (254, 243, 219),     # From Analyst Summary Box
            'text_dark': (31, 41, 55),    # High contrast charcoal
            'text_muted': (107, 114, 128),
            'border': (229, 231, 235),
            'white': (255, 255, 255)
        }
        self.l_margin_val = 15
        self.r_margin_val = 15
        self.set_margins(self.l_margin_val, 20, self.r_margin_val)
        self.content_width = 210 - self.l_margin_val - self.r_margin_val
        
        # Path to logo
        self.logo_path = os.path.join(os.getcwd(), 'assets', 'vein-logo-text.webp')

    def header(self):
        if self.page_no() == 1: return
        
        # Header background - Navy
        self.set_fill_color(*self.colors['navy'])
        self.rect(0, 0, self.w, 32, 'F')
        
        # Add Logo to Header
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=15, y=10, w=35)
        
        # Header Text
        self.set_xy(55, 12)
        self.set_text_color(*self.colors['white'])
        self.set_font('helvetica', 'B', 10)
        self.cell(0, 5, 'SUPPLY CHAIN INTELLIGENCE', ln=True)
        self.set_x(55)
        self.set_font('courier', 'B', 8)
        self.cell(0, 5, 'SECURE_DATA_FEED // ANALYST_VERIFIED', ln=False)
        
        self.set_xy(self.w - 45, 12)
        self.set_font('helvetica', 'B', 10)
        self.cell(30, 10, f'PAGE {self.page_no()}', align='R')
        self.set_y(40)

    def footer(self):
        if self.page_no() == 1: return
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(*self.colors['text_muted'])
        
        # Line separator
        self.set_draw_color(*self.colors['border'])
        self.line(self.l_margin_val, self.get_y(), self.w - self.r_margin_val, self.get_y())
        
        self.cell(self.content_width / 2, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d")}', align='L')
        
        # Add small logo to footer right
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=self.w - 40, y=self.h - 12, w=25)

    def add_title_page(self, ticker, date_str):
        self.add_page()
        
        # Top Accent Bar (Navy & Lime)
        self.set_fill_color(*self.colors['navy'])
        self.rect(0, 0, self.w, 20, 'F')
        self.set_fill_color(*self.colors['lime'])
        self.rect(0, 20, self.w, 2, 'F')
        
        # Center Logo
        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=(self.w/2)-40, y=60, w=80)
        
        self.set_y(110)
        self.set_font('helvetica', 'B', 32)
        self.set_text_color(*self.colors['text_dark'])
        self.multi_cell(self.content_width, 15, 'SUPPLY CHAIN\nINTELLIGENCE', align='C')
        
        self.ln(10)
        self.set_font('helvetica', 'B', 22)
        self.set_text_color(*self.colors['navy'])
        self.cell(self.content_width, 20, f'TICKER: {ticker}', ln=True, align='C')
        
        self.set_y(230)
        self.set_font('courier', 'B', 10)
        self.set_text_color(*self.colors['text_muted'])
        self.cell(self.content_width, 8, f'ANALYSIS_TIMESTAMP: {date_str.upper()}', ln=True, align='C')
        
        # Bottom Accent Bar
        self.set_fill_color(*self.colors['navy'])
        self.rect(0, self.h - 15, self.w, 15, 'F')

class MarkdownPDFGenerator:
    def __init__(self, ticker="UNKNOWN", date_str=""):
        self.pdf = VeinReportPDF()
        self.pdf.set_auto_page_break(auto=True, margin=25)
        self.pdf.add_title_page(ticker, date_str)
        self.colors = self.pdf.colors

    def _clean_line(self, text):
        if not text: return ""
        text = "".join(c for c in text if ord(c) < 256)
        return re.sub(r'\s{3,}', ' ', text).strip()

    def add_highlights_page(self, md_text):
        metrics = {"Recommendation": "N/A", "Action": "N/A", "Target": "N/A", "Sentiment": "N/A"}
        for line in md_text.split('\n'):
            if "Recommendation:" in line: metrics["Recommendation"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Action:" in line: metrics["Action"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Target Price:" in line: metrics["Target"] = line.split(":", 1)[1].strip().replace("**", "")

        self.pdf.add_page()
        self.pdf.set_font('helvetica', 'B', 22)
        self.pdf.set_text_color(*self.colors['navy'])
        self.pdf.cell(self.pdf.content_width, 15, "EXECUTIVE DASHBOARD", ln=True)
        
        # Grid using Analyst.png colors
        start_y = self.pdf.get_y()
        card_w = (self.pdf.content_width / 2) - 4
        
        for i, (label, val) in enumerate(metrics.items()):
            x = self.pdf.l_margin_val if i % 2 == 0 else (self.pdf.l_margin_val + card_w + 8)
            y = start_y + (i // 2) * 35
            
            # Use Cream background and Gold border
            self.pdf.set_fill_color(*self.colors['cream'])
            self.pdf.rect(x, y, card_w, 30, 'F')
            self.pdf.set_draw_color(*self.colors['gold'])
            self.pdf.set_line_width(0.5)
            self.pdf.rect(x, y, card_w, 30, 'D')
            
            self.pdf.set_xy(x + 5, y + 5)
            self.pdf.set_font('helvetica', 'B', 8)
            self.pdf.set_text_color(*self.colors['navy'])
            self.pdf.cell(0, 5, label.upper(), ln=True)
            
            self.pdf.set_xy(x + 5, y + 15)
            self.pdf.set_font('helvetica', 'B', 12)
            self.pdf.set_text_color(*self.colors['text_dark'])
            self.pdf.multi_cell(card_w - 10, 6, self._clean_line(val))
            
        self.pdf.set_y(start_y + 80)

    def add_markdown_content(self, md_text):
        lines = md_text.split('\n')
        in_table = False
        table_rows = []
        
        for line in lines:
            raw_line = line.strip()
            line = self._clean_line(raw_line)
            
            if not line or line == '---':
                if in_table: self._render_table(table_rows); table_rows = []; in_table = False
                continue

            if '|' in line and '---' in line:
                in_table = True; continue
            if '|' in line:
                in_table = True
                table_rows.append([p.strip() for p in line.split('|') if p.strip()])
                continue
            elif in_table:
                self._render_table(table_rows); table_rows = []; in_table = False

            self.pdf.set_x(self.pdf.l_margin_val)
            
            if raw_line.startswith('## '):
                self.pdf.ln(6)
                # Use Cream/Gold tab style for headers
                self.pdf.set_fill_color(*self.colors['cream'])
                self.pdf.rect(self.pdf.l_margin_val, self.pdf.get_y(), self.pdf.content_width, 10, 'F')
                self.pdf.set_xy(self.pdf.l_margin_val + 5, self.pdf.get_y() + 1)
                self.pdf.set_font('helvetica', 'B', 12)
                self.pdf.set_text_color(*self.colors['navy'])
                self.pdf.cell(0, 8, line[3:].upper())
                self.pdf.ln(12)
            
            elif raw_line.startswith('### '):
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.set_text_color(*self.colors['navy'])
                self.pdf.multi_cell(self.pdf.content_width, 8, line[4:])
            
            elif raw_line.startswith('- ') or raw_line.startswith('* '):
                self.pdf.set_x(self.pdf.l_margin_val + 5)
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.set_text_color(*self.colors['lime']) # Lime for bullet accents
                self.pdf.cell(5, 6, ">")
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text_dark'])
                self.pdf.multi_cell(self.pdf.content_width - 10, 6, line[2:])
            
            else:
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text_dark'])
                self.pdf.multi_cell(self.pdf.content_width, 6, line.replace("**", ""))

    def _render_table(self, rows):
        if not rows: return
        self.pdf.set_x(self.pdf.l_margin_val)
        # Use Navy for header row and Cream for rows
        with self.pdf.table(width=self.pdf.content_width, line_height=8, 
                            cell_fill_color=self.colors['cream'], cell_fill_mode="ROWS") as table:
            for i, row in enumerate(rows):
                r = table.row()
                self.pdf.set_font("helvetica", "B" if i == 0 else "", 9)
                self.pdf.set_text_color(*(self.colors['navy'] if i == 0 else self.colors['text_dark']))
                for cell in row:
                    r.cell(self._clean_line(cell))
        self.pdf.ln(4)

    def save(self, output_path):
        self.pdf.output(output_path)
        print(f"REPORT_SYNC_COMPLETE: {output_path}")
