from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCREENS = [
    (
        "01-sign-in.png",
        "Sign in",
        "Introduce the account journey; reveal the form, then choose a supplied sample account.",
    ),
    (
        "02-conversation.png",
        "Customer support",
        "Move from the account context into the verified answer and actual activity panel.",
    ),
    (
        "03-approval.png",
        "Explicit approval",
        "Pause on the account and case summary. Show approval before revealing the case receipt.",
    ),
    (
        "04-agent-studio.png",
        "Agent Studio",
        "Follow router, specialist and authorized tool. Reviewer mode is explicitly labeled here.",
    ),
    (
        "05-operations.png",
        "Operations",
        "Show measured requests, outcomes and integration usage; values come from persisted events.",
    ),
    (
        "06-execution-trace.png",
        "Execution evidence",
        "Open the side sheet and follow authorization, confirmation and the enterprise call.",
    ),
    (
        "07-evaluation.png",
        "Eight scenario results",
        "Run the suite and show all eight results. Each result expands into checks and traces.",
    ),
    ("08-mobile.png", "Mobile evaluation", "Show the responsive layout and persistent bottom navigation."),
    ("09-mobile-support.png", "Mobile support", "Show the same customer workflow at the mobile breakpoint."),
]


def build():
    out = ROOT / "output/pdf/relay-ui-guide.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out), pagesize=(1440, 900))
    pdf.setTitle("Relay - actual application UI and motion reference")
    pdf.setAuthor("Relay project")
    pdf.setFillColor(HexColor("#f7f8fa"))
    pdf.rect(0, 0, 1440, 900, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#375ac8"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(70, 825, "RELAY / UI REFERENCE")
    pdf.setFillColor(HexColor("#202631"))
    pdf.setFont("Helvetica-Bold", 44)
    pdf.drawString(70, 745, "The application, screen by screen.")
    pdf.setFont("Helvetica", 20)
    pdf.drawString(70, 697, "Actual Docker application captures. Nine named views, one view per page.")
    pdf.setFont("Helvetica", 16)
    pdf.drawString(
        70, 650, "These are implementation screenshots, not concept mockups. Source PNGs are in docs/ui/."
    )
    pdf.drawString(
        70,
        620,
        "The customer and staff screens were captured in Reviewer mode; live ADK evidence is separate.",
    )
    for i, (_, title, _) in enumerate(SCREENS):
        y = 552 - i * 43
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(75, y, f"{i + 1:02}  {title}")
        pdf.setFont("Helvetica", 15)
        pdf.drawRightString(1340, y, f"Page {i + 2}")
        pdf.linkRect("", f"screen-{i}", (70, y - 8, 1350, y + 24), relative=0, thickness=0)
    pdf.setFont("Helvetica", 14)
    pdf.drawString(
        70,
        75,
        "Motion suggestion: keep text readable, use short transitions, and hold on evidence and approval states.",
    )
    pdf.showPage()
    for i, (filename, title, note) in enumerate(SCREENS):
        source = ROOT / "docs/ui" / filename
        with Image.open(source) as image:
            w, h = image.size
        # Preserve a readable pixel scale rather than squeezing long screens onto A4.
        scale = min(1.0, 1300 / w)
        page_h = max(900, h * scale + 190)
        pdf.setPageSize((1440, page_h))
        pdf.bookmarkPage(f"screen-{i}")
        pdf.addOutlineEntry(title, f"screen-{i}")
        pdf.setFillColor(HexColor("#f7f8fa"))
        pdf.rect(0, 0, 1440, page_h, fill=1, stroke=0)
        pdf.setFillColor(HexColor("#375ac8"))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(60, page_h - 45, f"RELAY / {i + 1:02}")
        pdf.setFillColor(HexColor("#202631"))
        pdf.setFont("Helvetica-Bold", 28)
        pdf.drawString(60, page_h - 86, title)
        x = (1440 - w * scale) / 2
        y = page_h - 120 - h * scale
        pdf.drawImage(str(source), x, y, width=w * scale, height=h * scale)
        pdf.setFillColor(HexColor("#465063"))
        pdf.setFont("Helvetica", 13)
        pdf.drawString(60, 34, note)
        pdf.drawRightString(1380, 34, str(i + 2))
        pdf.showPage()
    pdf.save()
    print(out)


if __name__ == "__main__":
    build()
