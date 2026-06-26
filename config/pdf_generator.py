#!/usr/bin/env python3
"""
VEIN AI - PDF Report Generator v2.1
Upgraded to Tech-Noir / Dark Mode Aesthetic
"""

import os
import sys
from fpdf import FPDF
from datetime import datetime
from typing import Dict, List, Optional

# --- VEIN AI BRAND COLORS ---
C_BG = (11, 14, 20)          # Midnight Background
C_CARD = (22, 27, 34)        # Slightly lighter card background
C_CYAN = (0, 242, 255)       # Vein Cyan (Glow)
C_TEXT_MAIN = (224, 224, 224) # Off-white text
C_TEXT_DIM = (140, 140, 140) # Muted text
C_BULL = (0, 255, 136)       # Emerald Green
C_BEAR = (255, 76, 76)       # Warning Coral/Red

class VeinReportPDF(FPDF):
    def header(self):
        # Draw full page background on first page/new pages
        self.set_fill_color(*C_BG)
        self.rect(0, 0, 210, 297, 'F')
        
        # Glowing Top "Vein" Line
        self.set_draw_color(*C_CYAN)
        self.set_line_width(0.5)
        self.line(10, 15, 200, 15)
        
        # Logo / Brand
        self.set_xy(10, 18)
        self.set_text_color(*C_CYAN)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'VEIN AI // INTELLIGENCE FRAMEWORK', ln=True)
        
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*C_TEXT_DIM)
        self.cell(0, -2, 'DECENTRALIZED SUPPLY CHAIN ANALYSIS', ln=True)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Courier', 'I', 8)
        self.set_text_color(*C_TEXT_DIM)
        # Monospace terminal feel for footer
        status_msg = f"SYSTEM_OK // PAGE {self.page_no()} // HASH_{datetime.now().strftime('%H%M%S')}"
        self.cell(0, 10, status_msg, align='C')

    def draw_glass_card(self, x, y, w, h, title=""):
        """Draws a themed container for data."""
        self.set_fill_color(*C_CARD)
        self.set_draw_color(40, 45, 52) # Dark border
        self.rect(x, y, w, h, 'F')
        # Accent corner
        self.set_draw_color(*C_CYAN)
        self.line(x, y, x+5, y)
        self.line(x, y, x, y+5)
        
        if title:
            self.set_xy(x + 2, y + 2)
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(*C_CYAN)
            self.cell(0, 5, title.upper())

class PDFGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, data: Dict) -> str:
        ticker = data.get('entity', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"vein_report_{ticker}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        pdf = VeinReportPDF()
        pdf.add_page()
        
        # 1. TITLE SECTION
        pdf.set_y(40)
        pdf.set_text_color(*C_TEXT_MAIN)
        pdf.set_font('Helvetica', 'B', 24)
        pdf.cell(0, 10, f"ENTITY: {ticker}", ln=True)
        
        pdf.set_font('Courier', '', 10)
        pdf.set_text_color(*C_CYAN)
        pdf.cell(0, 10, f"REPORT_ID: {timestamp}-X92", ln=True)
        pdf.ln(5)

        # 2. SIGNAL DASHBOARD (The "Glass" Cards)
        # Signal Card
        signal = data.get('signal', 'HOLD')
        signal_color = C_BULL if signal == 'BUY' else C_BEAR if signal == 'SELL' else C_TEXT_MAIN
        
        pdf.draw_glass_card(10, 70, 60, 30, title="Market Signal")
        pdf.set_xy(10, 80)
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(*signal_color)
        pdf.cell(60, 15, signal, align='C')

        # Sentiment Card
        pdf.draw_glass_card(75, 70, 60, 30, title="Sentiment Score")
        pdf.set_xy(75, 80)
        pdf.set_font('Courier', 'B', 18)
        pdf.set_text_color(*C_TEXT_MAIN)
        pdf.cell(60, 15, f"{data.get('sentiment', 0.0):+.2f}", align='C')

        # Confidence Card
        pdf.draw_glass_card(140, 70, 60, 30, title="Confidence")
        pdf.set_xy(140, 80)
        pdf.set_font('Courier', 'B', 18)
        pdf.set_text_color(*C_TEXT_MAIN)
        pdf.cell(60, 15, f"{int(data.get('confidence', 0)*100)}%", align='C')

        # 3. EXECUTIVE SUMMARY
        pdf.set_xy(10, 110)
        pdf.set_text_color(*C_CYAN)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, "--- EXECUTIVE SUMMARY ---", ln=True)
        
        pdf.set_text_color(*C_TEXT_MAIN)
        pdf.set_font('Helvetica', '', 11)
        pdf.multi_cell(0, 6, data.get('summary', ''))
        pdf.ln(10)

        # 4. BULL / BEAR SPLIT
        y_pos = pdf.get_y()
        # Bull column
        pdf.draw_glass_card(10, y_pos, 92, 60, title="Bullish Vectors")
        pdf.set_xy(12, y_pos + 10)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*C_BULL)
        for factor in data.get('bull_factors', []):
            pdf.cell(90, 7, f"> {factor}", ln=True)
            pdf.set_x(12)

        # Bear column
        pdf.draw_glass_card(108, y_pos, 92, 60, title="Bearish Vectors")
        pdf.set_xy(110, y_pos + 10)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*C_BEAR)
        for factor in data.get('bear_factors', []):
            pdf.cell(90, 7, f"! {factor}", ln=True)
            pdf.set_x(110)

        # 5. SYSTEM FOOTNOTE
        pdf.set_y(y_pos + 70)
        pdf.set_font('Courier', 'I', 8)
        pdf.set_text_color(*C_TEXT_DIM)
        pdf.multi_cell(0, 4, "NOTICE: This intelligence report is processed via the Vein AI neural framework. Indicators are based on real-time supply chain telemetry and sentiment aggregation.")

        pdf.output(filepath)
        return filepath

if __name__ == "__main__":
    gen = PDFGenerator()
    test_data = {
        "entity": "NVDA",
        "summary": "NVIDIA is currently in a significant medium-term correction within a still-intact long-term uptrend. Momentum is deteriorating, but oversold conditions are building at the 200-day SMA support level.",
        "sentiment": -0.45,
        "signal": "SELL",
        "confidence": 0.82,
        "bull_factors": ["CUDA Ecosystem Moat", "Data Center Demand", "AI Secular Trend"],
        "bear_factors": ["Death Cross Precursor", "Accelerating Distribution", "MACD Negative Expansion"]
    }
    path = gen.generate_report(test_data)
    print(f"Report generated at: {path}")
