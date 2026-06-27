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
            'surface_2': (241, 245, 249),    # For table headers
            'border': (226, 232, 240),       # Light grey borders
            'text': (15, 23, 42),            # Midnight text
            'text_muted': (100, 116, 139),   # Slate grey text
            'primary': (0, 110, 255),        # Vein Azure
            'tradeable': (16, 185, 129),     # Emerald Green
            'chokepoint': (225, 29, 72),     # Rose/Coral Red
            'warning': (245, 158, 11),       # Amber
            'white': (255, 255, 255)
        }
        # SET STRICT MARGINS
        self.l_margin_val = 15
        self.r_margin_val = 15
        self.set_margins(self.l_margin_val, 20, self.r_margin_val)
        # Content width is strictly defined as (Page Width - Left Margin - Right Margin)
        self.content_width = 210 - self.l_margin_val - self.r_margin_val

    def header(self):
        if self.page_no() == 1: return
            
        # Full-width Azure Header bar
        self.set_fill_color(*self.colors['primary'])
        self.rect(0, 0, self.w, 30, 'F')
        
        self.set_xy(self.l_margin_val, 8)
        self.set_text_color(*self.colors['white'])
        self.set_font('helvetica', 'B', 14)
        self.cell(self.content_width, 8, 'Vein Explorer // INTELLIGENCE REPORT', ln=True)
        
        self.set_font('helvetica', '', 8)
        self.set_x(self.l_margin_val)
        self.cell(self.content_width, 4, 'SUPPLY CHAIN RISK ASSESSMENT FRAMEWORK', ln=False)
        
        self.set_xy(self.w - 45, 12)
        self.set_font('helvetica', 'B', 9)
        self.cell(30, 10, f'PAGE {self.page_no()}', ln=True, align='R')
        self.set_y(35) # Content starts exactly here

    def footer(self):
        if self.page_no() == 1: return
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(*self.colors['text_muted'])
        self.set_draw_color(*self.colors['border'])
        self.line(self.l_margin_val, self.get_y(), self.w - self.r_margin_val, self.get_y())
        self.cell(self.content_width, 10, f'Proprietary Intelligence Data | Vein Explorer | {datetime.now().strftime("%Y-%m-%d")}', align='C')

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
        self.set_font('helvetica', '', 12)
        self.cell(self.content_width, 8, f'Analysis Date: {date_str}', ln=True, align='C')
        self.cell(self.content_width, 8, 'Compiled by Vein Explorer Framework', ln=True, align='C')

class MarkdownPDFGenerator:
    def __init__(self, ticker="UNKNOWN", date_str=""):
        self.pdf = VeinReportPDF()
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.add_title_page(ticker, date_str)
        self.colors = self.pdf.colors

    def _clean_line(self, text):
        """CRITICAL: Removes emojis and collapses white-space that causes ghost columns in margins."""
        if not text: return ""
        # Remove characters not supported by standard fonts (emojis)
        text = "".join(c for c in text if ord(c) < 256)
        # Collapse 3 or more spaces into a single space (fixes margin drift)
        text = re.sub(r'\s{3,}', ' ', text)
        return text.strip()

    def _get_status_color(self, text):
        t = text.upper()
        if any(w in t for w in ["BUY", "BULLISH", "OVERWEIGHT", "POSITIVE", "KÖP", "HÅLL"]):
            return self.colors['tradeable']
        if any(w in t for w in ["SELL", "BEARISH", "NEGATIVE", "RISK", "DANGER", "SÄLJ", "UNDERWEIGHT"]):
            return self.colors['chokepoint']
        return self.colors['warning']

    def add_highlights_page(self, md_text):
        # Data Extraction
        metrics = {"Recommendation": "N/A", "Action": "N/A", "Target": "N/A", "Stop": "N/A", "Sentiment": "N/A"}
        for line in md_text.split('\n'):
            if "Recommendation:" in line or "Rekommendation:" in line: metrics["Recommendation"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Action:" in line or "Åtgärd:" in line: metrics["Action"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Target Price:" in line or "Målkurs:" in line: metrics["Target"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Stop Loss:" in line: metrics["Stop"] = line.split(":", 1)[1].strip().replace("**", "")

        self.pdf.add_page()
        self.pdf.set_font('helvetica', 'B', 20)
        self.pdf.set_text_color(*self.colors['text'])
        self.pdf.cell(self.pdf.content_width, 15, "Executive Highlights Dashboard", ln=True)
        
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
            self.pdf.set_font('helvetica', 'B', 12)
            self.pdf.set_text_color(*self._get_status_color(val))
            self.pdf.multi_cell(card_w - 10, 7, self._clean_line(val))
            
        self.pdf.set_y(start_y + (len(items) // 2 + 1) * 32 + 10)

    def add_markdown_content(self, md_text):
        lines = md_text.split('\n')
        in_table = False
        table_rows = []
        
        for line in lines:
            line = self._clean_line(line)
            if not line or line == '---':
                self.pdf.ln(2)
                continue

            # Table Management
            if '|' in line and '---' not in line:
                in_table = True
                table_rows.append([p.strip() for p in line.split('|') if p.strip()])
                continue
            elif in_table:
                self._render_table(table_rows)
                table_rows = []; in_table = False

            # HARD MARGIN RESET BEFORE EVERY BLOCK
            self.pdf.set_x(self.pdf.l_margin_val)
            
            if line.startswith('## '):
                self.pdf.ln(5)
                self.pdf.set_font('helvetica', 'B', 14)
                self.pdf.set_text_color(*self.colors['primary'])
                self.pdf.multi_cell(self.pdf.content_width, 10, line[3:].upper())
                self.pdf.ln(2)
            elif line.startswith('### '):
                self.pdf.set_font('helvetica', 'B', 11)
                self.pdf.set_text_color(*self.colors['text'])
                self.pdf.multi_cell(self.pdf.content_width, 8, line[4:])
            elif line.startswith('- ') or line.startswith('* '):
                self.pdf.set_x(self.pdf.l_margin_val + 5)
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.cell(5, 6, ">")
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.multi_cell(self.pdf.content_width - 10, 6, line[2:])
            else:
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text'])
                self.pdf.multi_cell(self.pdf.content_width, 6, line.replace("**", ""))

    def _render_table(self, rows):
        if not rows: return
        self.pdf.set_x(self.pdf.l_margin_val)
        self.pdf.set_font("helvetica", "B", 9)
        # Width is strictly locked to content_width
        with self.pdf.table(width=self.pdf.content_width, text_align="LEFT", line_height=7) as table:
            for i, row in enumerate(rows):
                r = table.row()
                if i == 0: self.pdf.set_fill_color(*self.colors['surface_2'])
                for cell in row:
                    r.cell(self._clean_line(cell))
        self.pdf.ln(5)

    def save(self, output_path):
        self.pdf.output(output_path)
        print(f"Vein Intelligence Report generated: {output_path}")

def get_latest_report():
    reports_dir = "reports"
    if not os.path.exists(reports_dir): return None
    subdirs = [os.path.join(reports_dir, d) for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
    if not subdirs: return None
    subdirs.sort(reverse=True)
    return subdirs[0]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a Vein Explorer PDF report.")
    parser.add_argument("input", nargs="?", help="Path to markdown file or folder.")
    parser.add_argument("-o", "--output", help="Output path.")
    
    args = parser.parse_args()
    input_path = args.input or get_latest_report()
    
    if not input_path or not os.path.exists(input_path):
        print("Error: No valid input found.")
        sys.exit(1)
    
    if os.path.isdir(input_path):
        md_path = os.path.join(input_path, "complete_report.md")
        ticker = os.path.basename(input_path.rstrip(os.sep)).split('_')[0]
        output_dir = input_path
    else:
        md_path = input_path
        ticker = os.path.basename(md_path).split('_')[0]
        output_dir = os.path.dirname(md_path) or "."

    date_str = datetime.now().strftime("%B %d, %Y")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
            
    generator = MarkdownPDFGenerator(ticker=ticker, date_str=date_str)
    generator.add_highlights_page(content)
    generator.add_markdown_content(content)
    
    out_file = args.output or os.path.join(output_dir, f"Vein_Report_{ticker}_{datetime.now().strftime('%H%M%S')}.pdf")
    generator.save(out_file)
