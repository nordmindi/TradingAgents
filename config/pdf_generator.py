#!/usr/bin/env python3
"""
Vein Explorer - PDF Report Generator
Professional Supply Chain Intelligence Reports
"""

import os
import sys
from fpdf import FPDF
from datetime import datetime
from typing import Dict, List, Optional

class VeinReportPDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        # Vein Explorer Brand Design System
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

    def draw_dashboard_card(self, x, y, width, height, label, value):
        """Draw a dashboard card with label and value."""
        self.set_fill_color(*self.colors['surface'])
        self.rect(x, y, width, height, 'F')
        self.set_draw_color(*self.colors['border'])
        self.rect(x, y, width, height, 'D')
        
        # Label
        self.set_xy(x + 5, y + 5)
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(*self.colors['text_muted'])
        self.cell(width - 10, 5, label.upper(), ln=True)
        
        # Value
        self.set_x(x + 5)
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(*self._get_status_color(str(value)))
        # Multi-cell prevents value overflow in boxes
        self.multi_cell(width - 10, 7, str(value))

class PDFGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, data: Dict) -> str:
        ticker = data.get('entity', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"Vein_Intelligence_Report_{ticker}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        date_str = datetime.now().strftime("%B %d, %Y")

        pdf = VeinReportPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_title_page(ticker, date_str)
        
        # Add highlights page
        self._add_highlights_page(pdf, data)
        
        # Add content page
        self._add_content_page(pdf, data)
        
        pdf.output(filepath)
        return filepath

    def _add_highlights_page(self, pdf, data):
        """Add executive highlights dashboard page."""
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 20)
        pdf.set_text_color(*pdf.colors['text'])
        pdf.cell(pdf.content_width, 15, "Executive Highlights Dashboard", ln=True)
        
        # Dashboard Cards (2-column layout)
        metrics = {
            "Signal": data.get('signal', 'N/A'),
            "Sentiment": f"{data.get('sentiment', 0.0):+.2f}",
            "Confidence": f"{int(data.get('confidence', 0)*100)}%",
            "Risk Level": data.get('risk_level', 'N/A')
        }
        
        start_y = pdf.get_y()
        items = list(metrics.items())
        # Calculate card width (content_width / 2 - padding)
        card_width = (pdf.content_width / 2) - 5
        card_height = 28
        card_spacing = 32
        
        for i, (label, val) in enumerate(items):
            x = 15 if i % 2 == 0 else (15 + card_width + 10)
            y = start_y + (i // 2) * card_spacing
            
            pdf.draw_dashboard_card(x, y, card_width, card_height, label, val)
            
        pdf.set_y(start_y + (len(items) // 2 + 1) * card_spacing + 10)

    def _add_content_page(self, pdf, data):
        """Add detailed content page."""
        pdf.add_page()
        
        # Executive Summary
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(*pdf.colors['primary'])
        pdf.cell(pdf.content_width, 10, "EXECUTIVE SUMMARY", ln=True)
        pdf.set_draw_color(*pdf.colors['primary'])
        pdf.line(15, pdf.get_y(), 70, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(*pdf.colors['text'])
        summary = data.get('summary', 'No summary available.')
        # Strip emojis from summary
        clean_summary = pdf._strip_emojis(summary)
        pdf.multi_cell(pdf.content_width, 6, clean_summary)
        pdf.ln(10)
        
        # Bullish Vectors
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(*pdf.colors['tradeable'])
        pdf.cell(pdf.content_width, 10, "BULLISH VECTORS", ln=True)
        pdf.ln(5)
        
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(*pdf.colors['text'])
        for factor in data.get('bull_factors', []):
            # Strip emojis from factor
            clean_factor = pdf._strip_emojis(factor)
            pdf.set_x(20)
            pdf.set_font('helvetica', 'B', 10)
            pdf.text(16, pdf.get_y() + 4, "•")
            pdf.set_font('helvetica', '', 10)
            pdf.multi_cell(pdf.content_width - 20, 6, clean_factor)
        pdf.ln(5)
        
        # Bearish Vectors
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(*pdf.colors['chokepoint'])
        pdf.cell(pdf.content_width, 10, "BEARISH VECTORS", ln=True)
        pdf.ln(5)
        
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(*pdf.colors['text'])
        for factor in data.get('bear_factors', []):
            # Strip emojis from factor
            clean_factor = pdf._strip_emojis(factor)
            pdf.set_x(20)
            pdf.set_font('helvetica', 'B', 10)
            pdf.text(16, pdf.get_y() + 4, "•")
            pdf.set_font('helvetica', '', 10)
            pdf.multi_cell(pdf.content_width - 20, 6, clean_factor)

if __name__ == "__main__":
    gen = PDFGenerator()
    test_data = {
        "entity": "NVDA",
        "summary": "NVIDIA is currently in a significant medium-term correction within a still-intact long-term uptrend. Momentum is deteriorating, but oversold conditions are building at the 200-day SMA support level.",
        "sentiment": -0.45,
        "signal": "SELL",
        "confidence": 0.82,
        "risk_level": "HIGH",
        "bull_factors": ["CUDA Ecosystem Moat", "Data Center Demand", "AI Secular Trend"],
        "bear_factors": ["Death Cross Precursor", "Accelerating Distribution", "MACD Negative Expansion"]
    }
    path = gen.generate_report(test_data)
    print(f"Report generated at: {path}")
