#!/usr/bin/env python3
"""
Generate PDF Guide for Proxy Rotator Dashboard
Usage: python3 generate_pdf_guide.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime

# Colors
PRIMARY_BLUE = HexColor('#1a365d')
SECONDARY_BLUE = HexColor('#2b6cb0')
ACCENT_GREEN = HexColor('#38a169')
ACCENT_PURPLE = HexColor('#805ad5')
LIGHT_GRAY = HexColor('#f7fafc')
DARK_GRAY = HexColor('#4a5568')

def create_pdf():
    filename = f"Proxy_Rotator_Guide_{datetime.now().strftime('%Y%m%d')}.pdf"

    # Page setup
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PRIMARY_BLUE,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=40,
        alignment=TA_CENTER
    )

    heading1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=PRIMARY_BLUE,
        spaceBefore=20,
        spaceAfter=15,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=SECONDARY_BLUE,
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceBefore=5,
        spaceAfter=10,
        leading=16,
        alignment=TA_JUSTIFY
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceBefore=3,
        spaceAfter=3,
        leftIndent=20,
        bulletIndent=10
    )

    code_style = ParagraphStyle(
        'CodeCustom',
        parent=styles['Normal'],
        fontSize=10,
        textColor=ACCENT_PURPLE,
        spaceBefore=5,
        spaceAfter=5,
        leftIndent=20,
        fontName='Courier'
    )

    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontSize=12,
        textColor=ACCENT_GREEN,
        spaceBefore=10,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    # Content
    story = []

    # ===== TITLE PAGE =====
    story.append(Spacer(1, 3*cm))

    # Logo/Title
    story.append(Paragraph("🚀", ParagraphStyle('Emoji', fontSize=60, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("PROXY ROTATOR", title_style))
    story.append(Paragraph("DASHBOARD GUIDE", title_style))
    story.append(Spacer(1, 1*cm))

    story.append(Paragraph("Panduan Lengkap Penggunaan", subtitle_style))
    story.append(Paragraph("Sistem Rotasi IP Otomatis untuk Submission", subtitle_style))
    story.append(Spacer(1, 2*cm))

    # Info box
    info_data = [
        ['📅 Tanggal', datetime.now().strftime('%d %B %Y')],
        ['🌐 Dashboard', 'https://proxy.rectoversomedia.com'],
        ['👤 Akun', 'Rectoverso Media'],
        ['📊 Status', 'AKTIF ✅'],
    ]

    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), PRIMARY_BLUE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 2, SECONDARY_BLUE),
        ('LINEBELOW', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
    ]))

    story.append(info_table)

    story.append(PageBreak())

    # ===== PAGE 2: OVERVIEW =====
    story.append(Paragraph("📋 OVERVIEW SISTEM", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Proxy Rotator Dashboard adalah sistem yang memungkinkan Anda untuk mengubah alamat IP "
        "setiap kali akan melakukan submission ke platform Prulady/VCBL. Dengan sistem ini, setiap submission "
        "akan menggunakan IP yang berbeda sehingga tidak terdeteksi sebagai bot.",
        body_style
    ))

    story.append(Spacer(1, 0.5*cm))

    # System Components
    story.append(Paragraph("Komponen Sistem:", heading2_style))

    components = [
        "🌐 <b>Proxy Dashboard</b> - Interface web untuk rotate IP",
        "🔄 <b>DataImpulse</b> - Provider proxy residential dengan 5GB traffic",
        "🌍 <b>Browser Chrome</b> - Browser dengan proxy extension",
        "📝 <b>Form Prulady</b> - Target submission form",
    ]

    for comp in components:
        story.append(Paragraph(f"• {comp}", bullet_style))

    story.append(Spacer(1, 0.5*cm))

    # Access Info
    story.append(Paragraph("🔑 Akses Login:", heading2_style))

    access_data = [
        ['Komponen', 'Detail'],
        ['🌐 Dashboard URL', 'https://proxy.rectoversomedia.com'],
        ['🔌 Proxy Host', 'gw.dataimpulse.com'],
        ['🔢 Proxy Port', '823'],
        ['👤 Username', '1598b06c2cd2aea9c80b'],
        ['🔐 Password', '4ffb48b7789c69a7'],
        ['💾 Traffic Tersedia', '5 GB (~500 submissions)'],
    ]

    access_table = Table(access_data, colWidths=[5*cm, 10*cm])
    access_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY_BLUE),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_GRAY]),
    ]))

    story.append(access_table)

    story.append(PageBreak())

    # ===== PAGE 3: SETUP CHROME =====
    story.append(Paragraph("⚙️ SETUP CHROME EXTENSION", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Langkah 1: Install Extension SwitchyOmega", heading2_style))
    story.append(Paragraph(
        "Extension ini memungkinkan Anda untuk switch proxy dengan mudah di Chrome.",
        body_style
    ))

    steps_1 = [
        "Buka Chrome dan kunjungi: <b>https://chrome.google.com/webstore</b>",
        "Cari: <b>\"SwitchyOmega\"</b> atau <b>\"Proxy SwitchyManager\"</b>",
        "Klik <b>\"Add to Chrome\"</b>",
        "Klik <b>\"Add extension\"</b> untuk konfirmasi",
    ]

    for i, step in enumerate(steps_1, 1):
        story.append(Paragraph(f"{i}. {step}", bullet_style))

    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Langkah 2: Setup Proxy Profile", heading2_style))

    steps_2 = [
        "Klik icon <b>SwitchyOmega</b> di pojok kanan atas Chrome",
        "Pilih <b>\"Options\"</b> atau <b>\"Create new profile\"</b>",
        "Isi profile baru dengan nama: <b>\"DataImpulse\"</b>",
        "Pada bagian <b>HTTP</b>, isi: <b>gw.dataimpulse.com</b>",
        "Pada bagian <b>Port</b>, isi: <b>823</b>",
        "SSL/HTTPS: <b>gw.dataimpulse.com:823</b>",
        "Klik <b>Save</b>",
    ]

    for i, step in enumerate(steps_2, 1):
        story.append(Paragraph(f"{i}. {step}", bullet_style))

    story.append(Spacer(1, 0.5*cm))

    # Screenshot placeholder
    story.append(Paragraph("📸 Contoh Setup:", heading2_style))
    screenshot_box = Table(
        [['[Screenshot: SwitchyOmega Options Page]']],
        colWidths=[14*cm]
    )
    screenshot_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_GRAY),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOX', (0, 0), (-1, -1), 1, DARK_GRAY),
    ]))
    story.append(screenshot_box)

    story.append(PageBreak())

    # ===== PAGE 4: WORKFLOW =====
    story.append(Paragraph("📋 WORKFLOW SUBMISSION", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    # Workflow diagram
    workflow_data = [
        ['Step', 'Aksi', 'Lokasi'],
        ['1', 'Buka Dashboard', 'https://proxy.rectoversomedia.com'],
        ['2', 'Aktifkan Proxy di Chrome', 'SwitchyOmega → DataImpulse'],
        ['3', 'Buka Form Prulady', 'vcbl.id/leads/register/prudential'],
        ['4', 'Input Data', 'Isi form sesuai data spreadsheet'],
        ['5', 'Submit Form', 'Klik tombol Submit'],
        ['6', 'Ganti IP', 'Dashboard → Klik "GANTI IP SEKARANG"'],
        ['7', 'Refresh Browser', 'Tekan F5 di Chrome'],
        ['8', 'Ulangi Step 3-7', 'Untuk data berikutnya'],
    ]

    workflow_table = Table(workflow_data, colWidths=[1.5*cm, 8*cm, 5*cm])
    workflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 2, ACCENT_PURPLE),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_GRAY]),
        ('TEXTCOLOR', (0, 6), (-1, 6), ACCENT_GREEN),  # Highlight step 6
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
    ]))

    story.append(workflow_table)

    story.append(Spacer(1, 0.5*cm))

    # Important Notes
    story.append(Paragraph("⚠️ PENTING:", heading2_style))

    notes = [
        "• <b>1 IP = 1 Submission</b> - Jangan submit 2x dengan IP yang sama",
        "• <b>Wajib Refresh</b> - Setelah ganti IP, refresh browser dulu",
        "• <b>Jeda 3-5 detik</b> - Jangan terlalu cepat antar submission",
        "• <b>Check Dashboard</b> - Pastikan IP sudah berubah sebelum submit lagi",
    ]

    for note in notes:
        story.append(Paragraph(note, bullet_style))

    story.append(Spacer(1, 0.5*cm))

    # Warning box
    warning_data = [
        ['⚠️ PERINGATAN'],
        ['Traffic DataImpulse terbatas 5GB (~500 submissions). Jika habis, hubungi admin untuk tambahan.'],
    ]

    warning_table = Table(warning_data, colWidths=[14*cm])
    warning_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f6ad55')),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#fefcbf')),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#744210')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 2, HexColor('#ed8936')),
    ]))

    story.append(warning_table)

    story.append(PageBreak())

    # ===== PAGE 5: TROUBLESHOOTING =====
    story.append(Paragraph("🔧 TROUBLESHOOTING", heading1_style))
    story.append(Spacer(1, 0.3*cm))

    # FAQ
    faq_data = [
        ['Problem', 'Solusi'],
        ['Proxy tidak connect', 'Check username & password. Pastikan dataimpulse.com:823'],
        ['IP tidak berubah', 'Klik tombol GANTI IP, tunggu 2 detik, refresh browser'],
        ['Dashboard error 500', 'SSH ke VPS, jalankan: systemctl restart proxy-rotator'],
        ['Traffic habis', 'Hubungi admin untuk tambahan quota'],
        ['Extension tidak muncul', 'Klik puzzle icon di Chrome, pin SwitchyOmega'],
        ['Auth popup muncul terus', 'Save credentials di Chrome autofill atau extension'],
    ]

    faq_table = Table(faq_data, colWidths=[6*cm, 9*cm])
    faq_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY_BLUE),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_GRAY]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(faq_table)

    story.append(Spacer(1, 0.5*cm))

    # Commands
    story.append(Paragraph("🔧 VPS Commands (Jika Error):", heading2_style))

    commands = [
        "systemctl restart proxy-rotator",
        "systemctl status proxy-rotator",
        "systemctl nginx restart",
        "ufw allow 5000/tcp",
    ]

    for cmd in commands:
        story.append(Paragraph(f"• <code>{cmd}</code>", code_style))

    story.append(Spacer(1, 0.5*cm))

    # Contact Info
    contact_data = [
        ['📞 Kontak Support'],
        ['Jika ada masalah teknis, hubungi IT Admin atau kirim ticket ke sistem support.'],
    ]

    contact_table = Table(contact_data, colWidths=[14*cm])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0fff4')),
        ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 2, ACCENT_GREEN),
    ]))

    story.append(contact_table)

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Dokumen ini di-generate secara otomatis pada {datetime.now().strftime('%d %B %Y, %H:%M')} | © Rectoverso Media",
        ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=DARK_GRAY, alignment=TA_CENTER)
    ))

    # Build PDF
    doc.build(story)
    print(f"✅ PDF berhasil dibuat: {filename}")
    return filename

if __name__ == "__main__":
    create_pdf()
