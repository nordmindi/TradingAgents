import os
import sys
import re
from datetime import datetime
from fpdf import FPDF
import json

class VeinReportPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        # Vein Brand Design System
        self.colors = {
            'background': (255, 255, 255),
            'surface': (249, 250, 251),      # Soft slate surface
            'surface_2': (241, 245, 249),    # For zebra rows
            'border': (226, 232, 240),       # Light grey borders
            'text': (15, 23, 42),            # Midnight text
            'text_muted': (100, 116, 139),   # Slate grey text
            'primary': (0, 110, 255),        # Vein Azure
            'tradeable': (16, 185, 129),     # Emerald Green
            'chokepoint': (225, 29, 72),     # Rose/Coral Red
            'warning': (245, 158, 11),       # Amber
            'white': (255, 255, 255)
        }
        self.l_margin_val = 15
        self.r_margin_val = 15
        self.set_margins(self.l_margin_val, 20, self.r_margin_val)
        self.content_width = 210 - self.l_margin_val - self.r_margin_val

    def header(self):
        if self.page_no() == 1: return
        self.set_fill_color(*self.colors['primary'])
        self.rect(0, 0, self.w, 30, 'F')
        self.set_xy(self.l_margin_val, 8)
        self.set_text_color(*self.colors['white'])
        self.set_font('helvetica', 'B', 14)
        self.cell(self.content_width, 8, 'VEIN EXPLORER // INTELLIGENCE REPORT', ln=True)
        self.set_font('courier', 'B', 8) # Terminal style for framework name
        self.set_x(self.l_margin_val)
        self.cell(self.content_width, 4, 'SYSTEM_STATUS: ACTIVE // DATA_STREAM: VERIFIED', ln=False)
        self.set_xy(self.w - 45, 12)
        self.set_font('helvetica', 'B', 9)
        self.cell(30, 10, f'PAGE {self.page_no()}', ln=True, align='R')
        self.set_y(35)

    def footer(self):
        if self.page_no() == 1: return
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(*self.colors['text_muted'])
        self.set_draw_color(*self.colors['border'])
        self.line(self.l_margin_val, self.get_y(), self.w - self.r_margin_val, self.get_y())
        self.cell(self.content_width, 10, f'Proprietary Intelligence Data | {datetime.now().strftime("%Y-%m-%d")}', align='C')

    def add_title_page(self, ticker, date_str):
        self.add_page()
        self.set_fill_color(*self.colors['primary'])
        self.rect(0, 0, self.w, 15, 'F')
        self.rect(0, self.h - 15, self.w, 15, 'F')
        self.set_y(100)
        self.set_text_color(*self.colors['text'])
        self.set_font('helvetica', 'B', 32)
        self.multi_cell(self.content_width, 15, 'SUPPLY CHAIN\nINTELLIGENCE', align='C')
        self.set_y(140)
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(*self.colors['primary'])
        self.cell(self.content_width, 20, f'TICKER: {ticker}', ln=True, align='C')
        self.set_y(220)
        self.set_text_color(*self.colors['text_muted'])
        self.set_font('courier', 'B', 12)
        self.cell(self.content_width, 8, f'ANALYSIS_DATE: {date_str.upper()}', ln=True, align='C')
        self.cell(self.content_width, 8, 'COMPILED_BY: VEIN_EXPLORER_V2', ln=True, align='C')

class MarkdownPDFGenerator:
    def __init__(self, ticker="UNKNOWN", date_str=""):
        self.pdf = VeinReportPDF()
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.add_title_page(ticker, date_str)
        self.colors = self.pdf.colors

    def _clean_line(self, text):
        if not text: return ""
        # Support specifically for arrows, otherwise strip unicode
        text = text.replace('↑', '^').replace('↓', 'v').replace('→', '>')
        text = "".join(c for c in text if ord(c) < 256)
        text = re.sub(r'\s{3,}', ' ', text)
        return text.strip()

    def _get_status_color(self, text):
        t = text.upper()
        if any(w in t for w in ["BUY", "BULLISH", "OVERWEIGHT", "POSITIVE", "UPTREND"]):
            return self.colors['tradeable'], " [^]"
        if any(w in t for w in ["SELL", "BEARISH", "NEGATIVE", "RISK", "DOWNTREND"]):
            return self.colors['chokepoint'], " [v]"
        return self.colors['warning'], " [>]"

    def draw_callout_box(self, title, text, status_text="INFO"):
        color, _ = self._get_status_color(status_text)
        self.pdf.ln(4)
        self.pdf.set_font('helvetica', '', 10)
        lines = self.pdf.multi_cell(self.pdf.content_width - 15, 6, text, split_only=True)
        height = (len(lines) * 6) + 12
        curr_y = self.pdf.get_y()
        # Card shadow/fill
        self.pdf.set_fill_color(252, 252, 252)
        self.pdf.rect(15, curr_y, self.pdf.content_width, height, 'F')
        # Leading accent line
        self.pdf.set_fill_color(*color)
        self.pdf.rect(15, curr_y, 1.5, height, 'F')
        self.pdf.set_xy(20, curr_y + 3)
        self.pdf.set_font('helvetica', 'B', 9)
        self.pdf.set_text_color(*color)
        self.pdf.cell(0, 5, title.upper(), ln=True)
        self.pdf.set_x(20)
        self.pdf.set_font('helvetica', '', 10)
        self.pdf.set_text_color(*self.colors['text'])
        self.pdf.multi_cell(self.pdf.content_width - 10, 6, self._clean_line(text))
        self.pdf.ln(4)

    def add_highlights_page(self, md_text):
        metrics = {"Recommendation": "N/A", "Action": "N/A", "Target": "N/A", "Stop": "N/A", "Sentiment": "N/A"}
        for line in md_text.split('\n'):
            if "Recommendation:" in line or "Rekommendation:" in line: metrics["Recommendation"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Action:" in line or "Åtgärd:" in line: metrics["Action"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Target Price:" in line or "Målkurs:" in line: metrics["Target"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Stop Loss:" in line: metrics["Stop"] = line.split(":", 1)[1].strip().replace("**", "")

        self.pdf.add_page()
        self.pdf.set_font('helvetica', 'B', 20)
        self.pdf.set_text_color(*self.colors['text'])
        self.pdf.cell(self.pdf.content_width, 15, "EXECUTIVE SUMMARY DASHBOARD", ln=True)
        
        start_y = self.pdf.get_y()
        items = list(metrics.items())
        card_w = (self.pdf.content_width / 2) - 5
        
        for i, (label, val) in enumerate(items):
            x = self.pdf.l_margin_val if i % 2 == 0 else (self.pdf.l_margin_val + card_w + 10)
            y = start_y + (i // 2) * 32
            
            self.pdf.set_fill_color(*self.colors['surface'])
            self.pdf.rect(x, y, card_w, 28, 'F')
            self.pdf.set_draw_color(*self.colors['border'])
            self.pdf.rect(x, y, card_w, 28, 'D')
            
            self.pdf.set_xy(x + 5, y + 5)
            self.pdf.set_font('helvetica', 'B', 8)
            self.pdf.set_text_color(*self.colors['text_muted'])
            self.pdf.cell(card_w - 10, 5, label.upper(), ln=True)
            
            self.pdf.set_x(x + 5)
            color, icon = self._get_status_color(val)
            self.pdf.set_font('helvetica', 'B', 12)
            self.pdf.set_text_color(*color)
            display_val = self._clean_line(val)
            if "N/A" not in display_val: display_val += icon
            self.pdf.multi_cell(card_w - 10, 7, display_val)
            
        self.pdf.set_y(start_y + (len(items) // 2 + 1) * 32 + 10)

    def add_markdown_content(self, md_text):
        lines = md_text.split('\n')
        in_table = False
        table_rows = []
        
        for line in lines:
            raw_line = line.strip()
            line = self._clean_line(raw_line)
            
            if not line or line == '---':
                if in_table: self._render_table(table_rows); table_rows = []; in_table = False
                self.pdf.ln(2)
                continue

            # Skip Table Separator
            if '|' in line and '---' in line:
                in_table = True
                continue

            if '|' in line:
                in_table = True
                table_rows.append([p.strip() for p in line.split('|') if p.strip()])
                continue
            elif in_table:
                self._render_table(table_rows); table_rows = []; in_table = False

            self.pdf.set_x(self.pdf.l_margin_val)
            
            if raw_line.startswith('## '):
                self.pdf.ln(6)
                self.pdf.set_font('helvetica', 'B', 14)
                self.pdf.set_text_color(*self.colors['primary'])
                txt = line[3:].upper()
                _, icon = self._get_status_color(txt)
                self.pdf.multi_cell(self.pdf.content_width, 10, f"{txt} {icon}")
                self.pdf.set_draw_color(*self.colors['primary'])
                self.pdf.line(15, self.pdf.get_y(), 45, self.pdf.get_y())
                self.pdf.ln(2)
            elif raw_line.startswith('### '):
                self.pdf.set_font('helvetica', 'B', 11)
                self.pdf.set_text_color(*self.colors['text'])
                self.pdf.multi_cell(self.pdf.content_width, 8, line[4:])
            elif "Action:" in raw_line or "Strategic" in raw_line:
                if ":" in line:
                    parts = line.split(":", 1)
                    self.draw_callout_box(parts[0], parts[1], status_text=parts[1])
            elif raw_line.startswith('- ') or raw_line.startswith('* '):
                self.pdf.set_x(self.pdf.l_margin_val + 5)
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.set_text_color(*self.colors['primary'])
                self.pdf.cell(5, 6, ">")
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text'])
                self.pdf.multi_cell(self.pdf.content_width - 10, 6, line[2:])
            else:
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text'])
                self.pdf.multi_cell(self.pdf.content_width, 6, line.replace("**", ""))

        if in_table: self._render_table(table_rows)

    def _render_table(self, rows):
        if not rows: return
        self.pdf.set_x(self.pdf.l_margin_val)
        with self.pdf.table(width=self.pdf.content_width, text_align="LEFT", line_height=8, 
                            cell_fill_color=self.colors['surface_2'], cell_fill_mode="ROWS") as table:
            for i, row in enumerate(rows):
                r = table.row()
                if i == 0:
                    self.pdf.set_font("helvetica", "B", 9)
                    self.pdf.set_fill_color(*self.colors['surface_2'])
                else:
                    self.pdf.set_font("helvetica", "", 9)
                for cell in row:
                    r.cell(self._clean_line(cell))
        self.pdf.ln(4)

    def save(self, output_path):
        self.pdf.output(output_path)
        print(f"Report Finalized: {output_path}")

# (Main execution block stays the same)
def get_latest_report():
    reports_dir = "reports"
    if not os.path.exists(reports_dir): return None
    subdirs = [os.path.join(reports_dir, d) for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
    if not subdirs: return None
    subdirs.sort(reverse=True)
    return subdirs[0]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?")
    args = parser.parse_args()
    
    input_path = args.input or get_latest_report()
    if os.path.isdir(input_path):
        md_path = os.path.join(input_path, "complete_report.md")
        ticker = os.path.basename(input_path.rstrip(os.sep)).split('_')[0]
        output_dir = input_path
    else:
        md_path = input_path
        ticker = os.path.basename(md_path).split('_')[0]
        output_dir = os.path.dirname(md_path) or "."

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
            
    generator = MarkdownPDFGenerator(ticker=ticker, date_str=datetime.now().strftime("%B %d, %Y"))
    generator.add_highlights_page(content)
    generator.add_markdown_content(content)
    
    out_file = os.path.join(output_dir, f"Vein_Report_{ticker}_{datetime.now().strftime('%H%M%S')}.pdf")
    generator.save(out_file)
