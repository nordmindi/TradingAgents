#!/usr/bin/env python3
"""
Professional PDF report generator for compact TradingAgents summaries.
"""

import os
from datetime import datetime
from typing import Dict

from fpdf import FPDF


class VeinReportPDF(FPDF):
    def __init__(self, orientation="P", unit="mm", format="A4"):
        super().__init__(orientation, unit, format)
        self.colors = {
            "white": (255, 255, 255),
            "ink": (17, 24, 39),
            "muted": (100, 116, 139),
            "border": (226, 232, 240),
            "surface": (248, 250, 252),
            "surface_alt": (241, 245, 249),
            "navy": (24, 54, 96),
            "navy_dark": (15, 35, 68),
            "blue": (37, 99, 235),
            "teal": (13, 148, 136),
            "amber": (217, 119, 6),
            "red": (190, 18, 60),
        }
        self.l_margin_val = 17
        self.r_margin_val = 17
        self.set_margins(self.l_margin_val, 22, self.r_margin_val)
        self.content_width = self.w - self.l_margin_val - self.r_margin_val

    def header(self):
        if self.page_no() == 1:
            return

        self.set_fill_color(*self.colors["navy_dark"])
        self.rect(0, 0, self.w, 24, "F")
        self.set_fill_color(*self.colors["teal"])
        self.rect(0, 24, self.w, 1.2, "F")

        self.set_xy(self.l_margin_val, 7.5)
        self.set_text_color(*self.colors["white"])
        self.set_font("helvetica", "B", 10)
        self.cell(self.content_width, 5, "TRADING INTELLIGENCE REPORT", ln=True)
        self.set_font("helvetica", "", 7.5)
        self.set_x(self.l_margin_val)
        self.cell(self.content_width, 4, "Evidence-based market summary", ln=False)

        self.set_xy(self.w - 43, 8)
        self.set_font("helvetica", "B", 8)
        self.cell(26, 7, f"PAGE {self.page_no()}", align="R")
        self.set_y(34)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_draw_color(*self.colors["border"])
        self.line(self.l_margin_val, self.get_y(), self.w - self.r_margin_val, self.get_y())
        self.set_font("helvetica", "", 7.5)
        self.set_text_color(*self.colors["muted"])
        self.cell(self.content_width / 2, 9, f"Generated {datetime.now().strftime('%Y-%m-%d')}", align="L")
        self.cell(self.content_width / 2, 9, "TradingAgents report package", align="R")

    def add_title_page(self, ticker, date_str):
        self.add_page()
        self.set_fill_color(*self.colors["navy_dark"])
        self.rect(0, 0, self.w, 28, "F")
        self.set_fill_color(*self.colors["teal"])
        self.rect(0, 28, self.w, 2, "F")
        self.set_fill_color(*self.colors["navy_dark"])
        self.rect(0, self.h - 18, self.w, 18, "F")

        self.set_y(88)
        self.set_text_color(*self.colors["ink"])
        self.set_font("helvetica", "B", 29)
        self.multi_cell(self.content_width, 12, "TRADING\nINTELLIGENCE REPORT", align="C")

        self.ln(8)
        self.set_font("helvetica", "B", 18)
        self.set_text_color(*self.colors["navy"])
        self.cell(self.content_width, 11, str(ticker), ln=True, align="C")

        self.set_font("helvetica", "", 10)
        self.set_text_color(*self.colors["muted"])
        self.cell(self.content_width, 7, f"Analysis date: {date_str}", ln=True, align="C")
        self.cell(self.content_width, 7, "Compiled by TradingAgents", ln=True, align="C")

    def clean_text(self, text):
        if not isinstance(text, str):
            text = str(text)
        return "".join(c for c in text if ord(c) < 256).strip()

    def status_color(self, value):
        text = str(value).upper()
        if any(word in text for word in ("BUY", "BULLISH", "OVERWEIGHT", "POSITIVE", "LOW")):
            return self.colors["teal"]
        if any(word in text for word in ("SELL", "BEARISH", "UNDERWEIGHT", "HIGH", "DANGER")):
            return self.colors["red"]
        return self.colors["amber"]

    def section_title(self, title, color_name="navy"):
        self.ln(5)
        y = self.get_y()
        self.set_draw_color(*self.colors[color_name])
        self.set_line_width(0.7)
        self.line(self.l_margin_val, y, self.l_margin_val + 22, y)
        self.ln(3)
        self.set_font("helvetica", "B", 13)
        self.set_text_color(*self.colors[color_name])
        self.multi_cell(self.content_width, 7, self.clean_text(title).upper())
        self.ln(1)

    def draw_dashboard_card(self, x, y, width, height, label, value):
        self.set_fill_color(*self.colors["surface"])
        self.rect(x, y, width, height, "F")
        self.set_draw_color(*self.colors["border"])
        self.set_line_width(0.35)
        self.rect(x, y, width, height, "D")

        self.set_xy(x + 5, y + 5)
        self.set_font("helvetica", "B", 7.5)
        self.set_text_color(*self.colors["muted"])
        self.cell(width - 10, 4, self.clean_text(label).upper(), ln=True)

        clean_value = self.clean_text(value)
        self.set_xy(x + 5, y + 14)
        self.set_font("helvetica", "B", 11 if len(clean_value) <= 34 else 9)
        self.set_text_color(*self.status_color(clean_value))
        self.multi_cell(width - 10, 5.4, clean_value)


class PDFGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, data: Dict) -> str:
        ticker = data.get("entity", "Unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"TradingAgents_Report_{ticker}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        date_str = datetime.now().strftime("%B %d, %Y")

        pdf = VeinReportPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_title_page(ticker, date_str)
        self._add_highlights_page(pdf, data)
        self._add_content_page(pdf, data)
        pdf.output(filepath)
        return filepath

    def _add_highlights_page(self, pdf, data):
        pdf.add_page()
        pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(*pdf.colors["ink"])
        pdf.cell(pdf.content_width, 10, "Executive Dashboard", ln=True)
        pdf.set_font("helvetica", "", 8.5)
        pdf.set_text_color(*pdf.colors["muted"])
        pdf.multi_cell(pdf.content_width, 5, "Compact summary of signal, sentiment, confidence, and risk.")
        pdf.ln(4)

        metrics = {
            "Signal": data.get("signal", "N/A"),
            "Sentiment": f"{data.get('sentiment', 0.0):+.2f}",
            "Confidence": f"{int(data.get('confidence', 0) * 100)}%",
            "Risk Level": data.get("risk_level", "N/A"),
        }

        start_y = pdf.get_y()
        card_width = (pdf.content_width - 8) / 2
        card_height = 31
        col_gap = 8
        row_gap = 7

        for i, (label, val) in enumerate(metrics.items()):
            x = pdf.l_margin_val if i % 2 == 0 else pdf.l_margin_val + card_width + col_gap
            y = start_y + (i // 2) * (card_height + row_gap)
            pdf.draw_dashboard_card(x, y, card_width, card_height, label, val)

        rows = (len(metrics) + 1) // 2
        pdf.set_y(start_y + rows * (card_height + row_gap) + 5)

    def _add_content_page(self, pdf, data):
        pdf.add_page()

        pdf.section_title("Executive Summary", "navy")
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(*pdf.colors["ink"])
        pdf.multi_cell(pdf.content_width, 5.8, pdf.clean_text(data.get("summary", "No summary available.")))
        pdf.ln(5)

        pdf.section_title("Bullish Vectors", "teal")
        self._render_factor_list(pdf, data.get("bull_factors", []))

        pdf.section_title("Bearish Vectors", "red")
        self._render_factor_list(pdf, data.get("bear_factors", []))

    def _render_factor_list(self, pdf, factors):
        if not factors:
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(*pdf.colors["muted"])
            pdf.multi_cell(pdf.content_width, 5.5, "No supported factors provided.")
            pdf.ln(2)
            return

        for factor in factors:
            pdf.set_x(pdf.l_margin_val + 3)
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(*pdf.colors["teal"])
            pdf.cell(4, 5.5, "-")
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(*pdf.colors["ink"])
            pdf.multi_cell(pdf.content_width - 7, 5.5, pdf.clean_text(factor))
            pdf.ln(0.5)


if __name__ == "__main__":
    gen = PDFGenerator()
    test_data = {
        "entity": "NVDA",
        "summary": (
            "NVIDIA is in a medium-term correction within a still-intact long-term "
            "uptrend. Momentum is deteriorating, while oversold conditions are "
            "building near major moving-average support."
        ),
        "sentiment": -0.45,
        "signal": "SELL",
        "confidence": 0.82,
        "risk_level": "HIGH",
        "bull_factors": ["CUDA ecosystem moat", "Data center demand", "AI secular trend"],
        "bear_factors": ["Momentum deterioration", "Valuation compression risk", "Event-risk sensitivity"],
    }
    path = gen.generate_report(test_data)
    print(f"Report generated at: {path}")
