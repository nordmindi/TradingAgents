import os
import re
from datetime import datetime

from fpdf import FPDF


class VeinReportPDF(FPDF):
    def __init__(self, orientation="P", unit="mm", format="A4", status_label="RESEARCH_OUTPUT"):
        super().__init__(orientation, unit, format)
        self.status_label = status_label
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
        self.content_width = 210 - self.l_margin_val - self.r_margin_val
        self.logo_path = os.path.join(os.getcwd(), "assets", "vein-logo-text.webp")

    def header(self):
        if self.page_no() == 1:
            return

        self.set_fill_color(*self.colors["navy_dark"])
        self.rect(0, 0, self.w, 25, "F")
        self.set_fill_color(*self.colors["teal"])
        self.rect(0, 25, self.w, 1.2, "F")

        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=17, y=8, w=29)

        self.set_xy(52, 8)
        self.set_text_color(*self.colors["white"])
        self.set_font("helvetica", "B", 9.5)
        self.cell(0, 5, "TRADING INTELLIGENCE REPORT", ln=True)
        self.set_x(52)
        self.set_font("helvetica", "", 7.5)
        self.cell(0, 4, f"VALIDATION STATUS // {self.status_label}", ln=False)

        self.set_xy(self.w - 43, 9)
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
        self.cell(self.content_width / 2, 9, "For research workflow review", align="R")

    def add_title_page(self, ticker, date_str):
        self.add_page()

        self.set_fill_color(*self.colors["navy_dark"])
        self.rect(0, 0, self.w, 28, "F")
        self.set_fill_color(*self.colors["teal"])
        self.rect(0, 28, self.w, 2, "F")

        if os.path.exists(self.logo_path):
            self.image(self.logo_path, x=(self.w / 2) - 37, y=52, w=74)

        self.set_y(105)
        self.set_font("helvetica", "B", 29)
        self.set_text_color(*self.colors["ink"])
        self.multi_cell(self.content_width, 12, "TRADING\nINTELLIGENCE REPORT", align="C")

        self.ln(8)
        self.set_font("helvetica", "B", 18)
        self.set_text_color(*self.colors["navy"])
        self.cell(self.content_width, 11, f"{ticker}", ln=True, align="C")

        self.set_font("helvetica", "", 10)
        self.set_text_color(*self.colors["muted"])
        self.cell(self.content_width, 7, f"Analysis timestamp: {date_str}", ln=True, align="C")
        self.cell(self.content_width, 7, f"Publication status: {self.status_label}", ln=True, align="C")

        self.set_fill_color(*self.colors["navy_dark"])
        self.rect(0, self.h - 18, self.w, 18, "F")


class MarkdownPDFGenerator:
    def __init__(self, ticker="UNKNOWN", date_str="", status_label="RESEARCH_OUTPUT"):
        self.pdf = VeinReportPDF(status_label=status_label)
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.add_title_page(ticker, date_str)
        self.colors = self.pdf.colors

    def _clean_line(self, text):
        if not text:
            return ""
        text = "".join(c for c in str(text) if ord(c) < 256)
        text = text.replace("**", "")
        return re.sub(r"\s{3,}", " ", text).strip()

    def add_highlights_page(self, md_text, dashboard_metrics=None):
        metrics = dashboard_metrics or self._metrics_from_markdown(md_text)

        self.pdf.add_page()
        self.pdf.set_font("helvetica", "B", 20)
        self.pdf.set_text_color(*self.colors["ink"])
        self.pdf.cell(self.pdf.content_width, 10, "Executive Dashboard", ln=True)

        self.pdf.set_font("helvetica", "", 8.5)
        self.pdf.set_text_color(*self.colors["muted"])
        self.pdf.multi_cell(
            self.pdf.content_width,
            5,
            "Canonical report summary generated from validation and final portfolio decision data.",
        )
        self.pdf.ln(4)

        start_y = self.pdf.get_y()
        card_w = (self.pdf.content_width - 8) / 2
        card_h = 31
        row_gap = 7
        col_gap = 8

        for i, (label, val) in enumerate(metrics.items()):
            x = self.pdf.l_margin_val if i % 2 == 0 else self.pdf.l_margin_val + card_w + col_gap
            y = start_y + (i // 2) * (card_h + row_gap)
            self._dashboard_card(x, y, card_w, card_h, label, val)

        rows = (len(metrics) + 1) // 2
        self.pdf.set_y(start_y + rows * (card_h + row_gap) + 5)

    def _dashboard_card(self, x, y, width, height, label, value):
        self.pdf.set_fill_color(*self.colors["surface"])
        self.pdf.rect(x, y, width, height, "F")
        self.pdf.set_draw_color(*self.colors["border"])
        self.pdf.set_line_width(0.35)
        self.pdf.rect(x, y, width, height, "D")

        self.pdf.set_xy(x + 5, y + 5)
        self.pdf.set_font("helvetica", "B", 7.5)
        self.pdf.set_text_color(*self.colors["muted"])
        self.pdf.cell(width - 10, 4, self._clean_line(label).upper(), ln=True)

        clean_value = self._clean_line(value)
        font_size = 11 if len(clean_value) <= 38 else 9
        self.pdf.set_xy(x + 5, y + 14)
        self.pdf.set_font("helvetica", "B", font_size)
        self.pdf.set_text_color(*self._value_color(label, clean_value))
        self.pdf.multi_cell(width - 10, 5.4, clean_value)

    def _value_color(self, label, value):
        text = f"{label} {value}".upper()
        if any(word in text for word in ("BLOCKED", "SELL", "UNDERWEIGHT", "HIGH RISK")):
            return self.colors["red"]
        if any(word in text for word in ("BUY", "OVERWEIGHT", "VERIFIED")):
            return self.colors["teal"]
        if any(word in text for word in ("WARNING", "RESEARCH", "HOLD")):
            return self.colors["amber"]
        return self.colors["ink"]

    def _metrics_from_markdown(self, md_text):
        metrics = {"Status": self.pdf.status_label, "Recommendation": "N/A", "Action": "N/A", "Target": "N/A"}
        for line in md_text.split("\n"):
            if "Rating:" in line:
                metrics["Recommendation"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Price Target:" in line:
                metrics["Target"] = line.split(":", 1)[1].strip().replace("**", "")
            if "Target Price:" in line:
                metrics["Target"] = line.split(":", 1)[1].strip().replace("**", "")
        if metrics["Recommendation"] != "N/A":
            metrics["Action"] = f"Use final Portfolio Manager rating: {metrics['Recommendation']}"
        return metrics

    def add_markdown_content(self, md_text):
        lines = md_text.split("\n")
        table_rows = []

        for raw in lines:
            raw_line = raw.strip()
            line = self._clean_line(raw_line)

            if not raw_line or raw_line == "---":
                if table_rows:
                    self._render_table(table_rows)
                    table_rows = []
                continue

            if "|" in raw_line and "---" in raw_line:
                continue
            if "|" in raw_line:
                table_rows.append([self._clean_line(p) for p in raw_line.split("|") if p.strip()])
                continue
            if table_rows:
                self._render_table(table_rows)
                table_rows = []

            self.pdf.set_x(self.pdf.l_margin_val)
            if raw_line.startswith("# "):
                self._render_h1(line[2:])
            elif raw_line.startswith("## "):
                self._render_h2(line[3:])
            elif raw_line.startswith("### "):
                self._render_h3(line[4:])
            elif raw_line.startswith("- ") or raw_line.startswith("* "):
                self._render_bullet(line[2:])
            else:
                self._render_paragraph(line)

        if table_rows:
            self._render_table(table_rows)

    def _render_h1(self, text):
        self.pdf.ln(5)
        self.pdf.set_font("helvetica", "B", 17)
        self.pdf.set_text_color(*self.colors["ink"])
        self.pdf.multi_cell(self.pdf.content_width, 8, self._clean_line(text))
        self.pdf.ln(2)

    def _render_h2(self, text):
        self.pdf.ln(7)
        y = self.pdf.get_y()
        self.pdf.set_draw_color(*self.colors["teal"])
        self.pdf.set_line_width(0.7)
        self.pdf.line(self.pdf.l_margin_val, y, self.pdf.l_margin_val + 22, y)
        self.pdf.ln(3)
        self.pdf.set_font("helvetica", "B", 13)
        self.pdf.set_text_color(*self.colors["navy"])
        self.pdf.multi_cell(self.pdf.content_width, 7, self._clean_line(text).upper())
        self.pdf.ln(1)

    def _render_h3(self, text):
        self.pdf.ln(3)
        self.pdf.set_font("helvetica", "B", 10.5)
        self.pdf.set_text_color(*self.colors["navy"])
        self.pdf.multi_cell(self.pdf.content_width, 6, self._clean_line(text))

    def _render_bullet(self, text):
        self.pdf.set_x(self.pdf.l_margin_val + 3)
        self.pdf.set_font("helvetica", "B", 9.5)
        self.pdf.set_text_color(*self.colors["teal"])
        self.pdf.cell(4, 5.5, "-")
        self.pdf.set_font("helvetica", "", 9.5)
        self.pdf.set_text_color(*self.colors["ink"])
        self.pdf.multi_cell(self.pdf.content_width - 7, 5.5, self._clean_line(text))
        self.pdf.ln(0.5)

    def _render_paragraph(self, text):
        if not text:
            return
        self.pdf.set_font("helvetica", "", 9.5)
        self.pdf.set_text_color(*self.colors["ink"])
        self.pdf.multi_cell(self.pdf.content_width, 5.6, self._clean_line(text))
        self.pdf.ln(1.2)

    def _render_table(self, rows):
        if not rows:
            return
        self.pdf.ln(2)
        self.pdf.set_x(self.pdf.l_margin_val)
        with self.pdf.table(
            width=self.pdf.content_width,
            line_height=7,
            cell_fill_color=self.colors["surface"],
            cell_fill_mode="ROWS",
            borders_layout="SINGLE_TOP_LINE",
        ) as table:
            for i, row in enumerate(rows):
                r = table.row()
                self.pdf.set_font("helvetica", "B" if i == 0 else "", 8.2)
                self.pdf.set_text_color(*(self.colors["navy"] if i == 0 else self.colors["ink"]))
                for cell in row:
                    r.cell(self._clean_line(cell))
        self.pdf.ln(4)

    def save(self, output_path):
        self.pdf.output(output_path)
        print(f"REPORT_SYNC_COMPLETE: {output_path}")
