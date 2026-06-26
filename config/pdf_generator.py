#!/usr/bin/env python3
"""
PDF Report Generator v2.0 - Analysis Service
Generates premium intelligence reports in PDF format.
"""

import os
import sys
from fpdf import FPDF
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../shared'))
from database_client import get_db_client

class AnalystReportPDF(FPDF):
    def header(self):
        # Brand Colors
        self.set_fill_color(22, 27, 34) # Dark background
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 20)
        self.cell(0, 15, 'BULLION ANALYTICS', ln=True, align='L')
        
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, 'Premium Intelligence & Risk Assessment', ln=True, align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Proprietary & Confidential | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', align='C')

class PDFGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """Load report templates from config file."""
        config_path = os.path.join(os.path.dirname(__file__), '../../config/report_templates.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f).get('report_templates', {})
            except Exception as e:
                print(f"[ERROR] Failed to load report templates: {e}")
        return {}

    def _find_template(self, ticker: str) -> Optional[Dict]:
        """Find a template that contains the given ticker."""
        for key, template in self.templates.items():
            if ticker in template.get('tickers', []):
                return template
        return None

    def generate_report(self, data: Dict) -> str:
        """
        Generate a PDF report from analysis data.
        """
        ticker = data.get('entity', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"report_{ticker}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        db = get_db_client()
        macro_data = {}
        try:
            # Fetch latest G/S Ratio
            gs_res = db.fetch_one("SELECT value FROM market_indicators WHERE indicator_name = 'GOLD_SILVER_RATIO' ORDER BY timestamp DESC LIMIT 1")
            if gs_res:
                macro_data['gs_ratio'] = float(gs_res['value'])
        finally:
            db.close()

        pdf = AnalystReportPDF()
        pdf.add_page()
        
        # Reset text color for body
        pdf.set_text_color(22, 27, 34)
        
        # Title Section
        pdf.set_font('helvetica', 'B', 18)
        pdf.cell(0, 15, f'Market Intelligence Report: {ticker}', ln=True)
        
        # Template Info
        template = self._find_template(ticker)
        if template:
            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(37, 99, 235) # Blue accent
            pdf.cell(0, 8, template.get('name', ''), ln=True)
            pdf.set_font('helvetica', 'I', 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, template.get('description', ''), ln=True)
        
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f'Generated on {datetime.now().strftime("%B %d, %Y")}', ln=True)
        pdf.ln(10)
        
        # Macro Overview Widget
        if 'gs_ratio' in macro_data:
            pdf.set_fill_color(245, 247, 250)
            pdf.rect(10, pdf.get_y(), 190, 20, 'F')
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(22, 27, 34)
            pdf.cell(95, 10, 'Macro Indicator: Gold/Silver Ratio', ln=0)
            pdf.set_font('helvetica', 'B', 14)
            pdf.cell(95, 10, f"{macro_data['gs_ratio']:.2f}", ln=1, align='R')
            pdf.set_font('helvetica', 'I', 8)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 5, 'Indicates relative value between precious metals. >80 often suggests silver is undervalued.', ln=1)
            pdf.ln(10)

        # Summary Section
        pdf.set_text_color(22, 27, 34)
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, 'EXECUTIVE SUMMARY', ln=True)
        pdf.set_draw_color(37, 99, 235) # Blue accent
        pdf.line(10, pdf.get_y(), 60, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, data.get('summary', 'No summary available.'))
        pdf.ln(8)
        
        # Metrics & Signal
        pdf.set_fill_color(240, 244, 255)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, ' ANALYSIS METRICS', ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(60, 10, 'Metric', border='B')
        pdf.cell(60, 10, 'Value', border='B', ln=True)
        
        pdf.set_font('helvetica', '', 11)
        sentiment = data.get('sentiment', 0.0)
        signal = data.get('signal', 'HOLD')
        
        # Signal Color logic
        if signal == 'BUY':
            pdf.set_text_color(16, 185, 129) # Emerald
        elif signal == 'SELL':
            pdf.set_text_color(239, 68, 68) # Red
        else:
            pdf.set_text_color(22, 27, 34)

        metrics = [
            ('Composite Sentiment', f"{sentiment:+.2f}"),
            ('Signal Strategy', signal),
            ('Confidence Level', f"{round(data.get('confidence', 0.5) * 100, 1)}%"),
        ]
        
        for metric, value in metrics:
            pdf.set_text_color(100, 100, 100)
            pdf.cell(60, 10, metric, border='B')
            if metric == 'Signal Strategy':
                if signal == 'BUY': pdf.set_text_color(16, 185, 129)
                elif signal == 'SELL': pdf.set_text_color(239, 68, 68)
                else: pdf.set_text_color(22, 27, 34)
            else:
                pdf.set_text_color(22, 27, 34)
            pdf.cell(60, 10, str(value), border='B', ln=True)
            
        # Add Weight Info if template used
        if template:
            pdf.ln(5)
            pdf.set_font('helvetica', 'I', 8)
            pdf.set_text_color(128, 128, 128)
            weights = [
                f"Sentiment: {template.get('weight_sentiment', 0)*100}%",
                f"Price: {template.get('weight_price', 0)*100}%",
                f"Social: {template.get('weight_social', 0)*100}%",
                f"News: {template.get('weight_news', 0)*100}%"
            ]
            pdf.cell(0, 5, f"Analysis Weights Used: {' | '.join([w for w in weights if '0%' not in w])}", ln=True)

        pdf.ln(10)
        
        # Bull/Bear Factors
        pdf.set_text_color(22, 27, 34)
        pdf.set_font('helvetica', 'B', 13)
        pdf.cell(95, 10, ' BULL FACTORS', border=0, ln=0)
        pdf.cell(95, 10, ' BEAR FACTORS', border=0, ln=1)
        
        pdf.set_font('helvetica', '', 10)
        bulls = data.get('bull_factors', [])
        bears = data.get('bear_factors', [])
        
        max_factors = max(len(bulls), len(bears))
        for i in range(max_factors):
            b_text = f"+ {bulls[i]}" if i < len(bulls) else ""
            r_text = f"- {bears[i]}" if i < len(bears) else ""
            
            pdf.set_text_color(16, 185, 129)
            pdf.cell(95, 7, b_text, ln=0)
            pdf.set_text_color(239, 68, 68)
            pdf.cell(95, 7, r_text, ln=1)
            
        pdf.output(filepath)
        return filepath

if __name__ == "__main__":
    # Test
    gen = PDFGenerator()
    test_data = {
        "entity": "BOL.ST",
        "summary": "Boliden AB shows strong recovery signals despite moderate market volatility. Sentiment is driven by copper price appreciation and positive analyst revisions.",
        "sentiment": 0.45,
        "signal": "BUY",
        "confidence": 0.78,
        "bull_factors": ["Rising copper prices", "Strong balance sheet", "High ESG rating"],
        "bear_factors": ["Operational costs rising", "Regulatory uncertainty in Finland"]
    }
    path = gen.generate_report(test_data)
    print(f"Report generated at: {path}")
