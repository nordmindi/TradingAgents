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
            'primary': (0, 110, 255),       # Vein Azure
            'tradeable': (16, 185, 129),     # Emerald Green
            'chokepoint': (225, 29, 72),     # Rose/Coral Red
            'warning': (245, 158, 11),       # Amber
            'white': (255, 255, 255)
        }
        self.set_margins(15, 20, 15) # Standardized margins (Left, Top, Right)
        # Calculate content width (page width - left margin - right margin)
        self.content_width = self.w - 15 - 15

    def header(self):
        if self.page_no() == 1: return
            
        # Full-width Azure Header bar
        self.set_fill_color(*self.colors['primary'])
        self.rect(0, 0, self.w, 30, 'F')
        
        self.set_xy(15, 8)
        self.set_text_color(*self.colors['white'])
        self.set_font('helvetica', 'B', 14)
        self.cell(self.content_width, 8, 'Vein Explorer // INTELLIGENCE REPORT', ln=True)
        
        self.set_font('helvetica', '', 8)
        self.set_x(15)
        self.cell(self.content_width, 4, 'SUPPLY CHAIN RISK ASSESSMENT FRAMEWORK', ln=False)
        
        self.set_xy(self.w - 45, 12)
        self.set_font('helvetica', 'B', 9)
        self.cell(30, 10, f'PAGE {self.page_no()}', ln=True, align='R')
        self.set_y(35) # Ensure content starts below header

    def footer(self):
        if self.page_no() == 1: return
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(*self.colors['text_muted'])
        # Draw a thin separator
        self.set_draw_color(*self.colors['border'])
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.cell(self.content_width, 10, f'Proprietary Intelligence Data | Vein Explorer | {datetime.now().strftime("%Y-%m-%d")}', align='C')

    def add_title_page(self, ticker, date_str):
        self.add_page()
        # Header/Footer decorative azure bars
        self.set_fill_color(*self.colors['primary'])
        self.rect(0, 0, self.w, 15, 'F')
        self.rect(0, self.h - 15, self.w, 15, 'F')
        
        self.set_y(100)
        self.set_text_color(*self.colors['text'])
        self.set_font('helvetica', 'B', 32)
        # multi_cell prevents the title from ever going off page
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

    def _strip_emojis(self, text):
        """Remove emojis and other unicode characters not supported by helvetica font."""
        if not isinstance(text, str):
            return str(text)
        # Remove emojis and other unicode characters outside basic ASCII range
        return "".join(c for c in text if ord(c) < 256)

    def _get_status_color(self, text):
        t = text.upper()
        if any(w in t for w in ["BUY", "ACCUMULATE", "BULLISH", "OVERWEIGHT", "POSITIVE"]):
            return self.colors['tradeable']
        if any(w in t for w in ["SELL", "UNDERWEIGHT", "BEARISH", "NEGATIVE", "RISK", "DANGER"]):
            return self.colors['chokepoint']
        return self.colors['warning']

    def draw_callout_box(self, title, text, status_text="INFO"):
        """Draws a professional wrapped callout box for Strategic Actions."""
        # Remove unicode characters that aren't supported by helvetica
        clean_text = self._strip_emojis(text)
        clean_title = self._strip_emojis(title)
        
        color = self._get_status_color(status_text)
        self.pdf.ln(5)
        
        # Calculate Height
        self.pdf.set_font('helvetica', '', 10)
        # Use multi_cell split_only to calculate height before drawing
        lines = self.pdf.multi_cell(self.pdf.content_width - 20, 6, clean_text, split_only=True)
        height = (len(lines) * 6) + 12

        curr_y = self.pdf.get_y()
        # Box background
        self.pdf.set_fill_color(252, 252, 252)
        self.pdf.rect(15, curr_y, self.pdf.content_width, height, 'F')
        # Left Accent Border
        self.pdf.set_fill_color(*color)
        self.pdf.rect(15, curr_y, 2, height, 'F')
        
        # Title
        self.pdf.set_xy(20, curr_y + 3)
        self.pdf.set_font('helvetica', 'B', 9)
        self.pdf.set_text_color(*color)
        self.pdf.cell(self.pdf.content_width - 20, 5, clean_title.upper(), ln=True)
        
        # Content
        self.pdf.set_x(20)
        self.pdf.set_font('helvetica', '', 10)
        self.pdf.set_text_color(*self.colors['text'])
        self.pdf.multi_cell(self.pdf.content_width - 20, 6, clean_text)
        self.pdf.ln(5)

    def add_highlights_page(self, md_text):
        # Extract metrics (same logic as before)
        metrics = {"Recommendation": "N/A", "Action": "N/A", "Target": "N/A", "Stop": "N/A", "Sentiment": "N/A"}
        for line in md_text.split('\n'):
            clean_line = self._strip_emojis(line)
            if "Recommendation:" in clean_line or "Rekommendation:" in clean_line: metrics["Recommendation"] = clean_line.split(":", 1)[1].strip().replace("**", "")
            if "Action:" in clean_line or "Åtgärd:" in clean_line: metrics["Action"] = clean_line.split(":", 1)[1].strip().replace("**", "")
            if "Target Price:" in clean_line or "Målkurs:" in clean_line: metrics["Target"] = clean_line.split(":", 1)[1].strip().replace("**", "")
            if "Stop Loss:" in clean_line: metrics["Stop"] = clean_line.split(":", 1)[1].strip().replace("**", "")

        self.pdf.add_page()
        self.pdf.set_font('helvetica', 'B', 20)
        self.pdf.set_text_color(*self.colors['text'])
        self.pdf.cell(self.pdf.content_width, 15, "Executive Highlights Dashboard", ln=True)
        
        # Dashboard Cards (2-column layout)
        start_y = self.pdf.get_y()
        items = list(metrics.items())
        # Calculate card width (content_width / 2 - padding)
        card_width = (self.pdf.content_width / 2) - 5
        card_height = 28
        card_spacing = 32
        
        for i, (label, val) in enumerate(items):
            x = 15 if i % 2 == 0 else (15 + card_width + 10)
            y = start_y + (i // 2) * card_spacing
            
            self.pdf.set_fill_color(*self.colors['surface'])
            self.pdf.rect(x, y, card_width, card_height, 'F')
            self.pdf.set_draw_color(*self.colors['border'])
            self.pdf.rect(x, y, card_width, card_height, 'D')
            
            self.pdf.set_xy(x + 5, y + 5)
            self.pdf.set_font('helvetica', 'B', 8)
            self.pdf.set_text_color(*self.colors['text_muted'])
            self.pdf.cell(card_width - 10, 5, label.upper(), ln=True)
            
            self.pdf.set_x(x + 5)
            self.pdf.set_font('helvetica', 'B', 12)
            self.pdf.set_text_color(*self._get_status_color(val))
            # Multi-cell prevents value overflow in boxes
            self.pdf.multi_cell(card_width - 10, 7, val)
            
        self.pdf.set_y(start_y + (len(items) // 2 + 1) * card_spacing + 10)

    def add_markdown_content(self, md_text):
        lines = md_text.split('\n')
        in_table = False
        table_rows = []
        
        for line in lines:
            line = line.strip()
            if not line:
                self.pdf.ln(2)
                continue

            # Check for Table
            clean_line = self._strip_emojis(line)
            if '|' in clean_line and '---' not in clean_line:
                in_table = True
                table_rows.append([self._strip_emojis(p.strip()) for p in clean_line.split('|') if p.strip()])
                continue
            elif in_table:
                self._render_table(table_rows)
                table_rows = []; in_table = False

            # Header Styling (Fixing overflow with multi_cell)
            if line.startswith('## '):
                self.pdf.ln(5)
                self.pdf.set_font('helvetica', 'B', 14)
                self.pdf.set_text_color(*self.colors['primary'])
                clean_header = self._strip_emojis(line[3:].upper())
                self.pdf.multi_cell(self.pdf.content_width, 10, clean_header)
                self.pdf.set_draw_color(*self.colors['primary'])
                self.pdf.line(15, self.pdf.get_y(), 60, self.pdf.get_y())
                self.pdf.ln(3)
            
            elif line.startswith('### '):
                self.pdf.set_font('helvetica', 'B', 11)
                self.pdf.set_text_color(*self.colors['text'])
                clean_subheader = self._strip_emojis(line[4:])
                self.pdf.multi_cell(self.pdf.content_width, 8, clean_subheader)
                
            # STRATEGIC ACTIONS HANDLING
            elif "Strategic Action" in line or "Action:" in line:
                parts = line.split(":", 1)
                title = parts[0].replace("**", "").strip()
                content = parts[1].replace("**", "").strip()
                # Strip emojis from title and content
                clean_title = self._strip_emojis(title)
                clean_content = self._strip_emojis(content)
                self.draw_callout_box(clean_title, clean_content, status_text=clean_content)

            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                self.pdf.set_x(20)
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text'])
                # Bullet character
                self.pdf.set_font('helvetica', 'B', 10)
                self.pdf.text(16, self.pdf.get_y() + 4, ">")
                self.pdf.set_font('helvetica', '', 10)
                clean_bullet = self._strip_emojis(line[2:])
                self.pdf.multi_cell(self.pdf.content_width - 20, 6, clean_bullet)
            
            # Regular Paragraphs
            else:
                self.pdf.set_font('helvetica', '', 10)
                self.pdf.set_text_color(*self.colors['text'])
                clean_line = line.replace("**", "")
                # Strip emojis and unsupported unicode characters
                clean_line = self._strip_emojis(clean_line)
                self.pdf.multi_cell(self.pdf.content_width, 6, clean_line)

    def _render_table(self, rows):
        if not rows: return
        # Strip emojis from all table content
        clean_rows = []
        for row in rows:
            clean_row = [self._strip_emojis(cell) for cell in row]
            clean_rows.append(clean_row)
        
        self.pdf.set_font("helvetica", "B", 9)
        with self.pdf.table(width=self.pdf.content_width, col_widths=None, text_align="LEFT", line_height=7) as table:
            for i, row in enumerate(clean_rows):
                r = table.row()
                if i == 0: # Header
                    self.pdf.set_fill_color(*self.colors['surface_2'])
                    for cell in row: r.cell(cell)
                else:
                    for cell in row: r.cell(cell)
        self.pdf.ln(5)

    def save(self, output_path):
        self.pdf.output(output_path)

# (Rest of your execution logic / argparse stays same)
        print(f"Vein Explorer report generated: {output_path}")

def get_latest_report():
    reports_dir = "reports"
    if not os.path.exists(reports_dir): return None
    subdirs = [os.path.join(reports_dir, d) for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
    if not subdirs: return None
    subdirs.sort(reverse=True)
    return subdirs[0]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a Vein Explorer PDF report from a markdown file.")
    parser.add_argument("input", nargs="?", help="Path to the markdown file or a directory containing complete_report.md")
    parser.add_argument("-o", "--output", help="Optional output path for the PDF")
    
    args = parser.parse_args()
    
    input_path = args.input
    if not input_path:
        # Fallback to latest report in reports/
        report_dir = get_latest_report()
        if not report_dir:
            print("No reports found in the 'reports/' directory.")
            print("Usage: python scripts/generate_full_report_pdf.py [path_to_markdown_or_folder]")
            sys.exit(1)
        input_path = report_dir
    
    # Resolve the markdown file path
    if os.path.isdir(input_path):
        md_path = os.path.join(input_path, "complete_report.md")
        ticker = os.path.basename(input_path.rstrip(os.sep)).split('_')[0]
        output_dir = input_path
    else:
        md_path = input_path
        ticker = os.path.basename(md_path).split('_')[0]
        output_dir = os.path.dirname(md_path) or "."
        
    if not os.path.exists(md_path):
        print(f"Error: Markdown file not found at {md_path}")
        sys.exit(1)
        
    date_str = datetime.now().strftime("%B %d, %Y")
    print(f"Generating Vein Explorer PDF for {ticker} from {md_path}...")
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        generator = MarkdownPDFGenerator(ticker=ticker, date_str=date_str)
        generator.add_highlights_page(content)
        generator.add_markdown_content(content)
        
        if args.output:
            output_path = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"Vein_Intelligence_Report_{ticker}_{timestamp}.pdf"
            output_path = os.path.join(output_dir, output_filename)
        
        generator.save(output_path)
    except Exception as e:
        print(f"Critical Error during PDF generation: {e}")
        sys.exit(1)
