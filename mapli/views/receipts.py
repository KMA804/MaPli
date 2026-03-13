# receipts.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone  # ← À ajouter si nécessaire

def generate_appointment_receipt(appointment):
    """Génère le PDF du reçu de rendez-vous avec l'heure sélectionnée"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#0d6efd'),
            alignment=1,  # Centré
            spaceAfter=30
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12
        )
        
        normal_style = styles['Normal']
        
        # Contenu du PDF
        story = []
        
        # En-tête
        story.append(Paragraph("MaPli - RECU ÉCHOGRAPHIE", title_style))
        story.append(Spacer(1, 5))
        
        # Ligne de séparation
        story.append(Paragraph("<hr/>", normal_style))
        story.append(Spacer(1, 5))
        
        # Informations patient
        story.append(Paragraph("INFORMATIONS PATIENT :", header_style))
        patient_data = [
            ["• Nom :", appointment.patient_name],
            ["• Email :", appointment.patient_email],
            ["• Téléphone :", appointment.patient_phone]
        ]
        patient_table = Table(patient_data, colWidths=[60*mm, 100*mm])
        patient_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 5))
        
        # Détails rendez-vous
        story.append(Paragraph("DÉTAILS RENDEZ-VOUS :", header_style))
        
        # Formatage de la date et heure sélectionnée
        scheduled_date = appointment.scheduled_date
        date_formatted = scheduled_date.strftime("%d/%m/%Y")
        time_formatted = scheduled_date.strftime("%H:%M")
        
        # Gestion du type d'échographie
        ultrasound_type_display = appointment.ultrasound_type
        if hasattr(appointment, 'get_ultrasound_type_display'):
            try:
                ultrasound_type_display = appointment.get_ultrasound_type_display()
            except:
                pass
        
        appointment_data = [
            ["• Numéro :", str(appointment.registration_number)],
            ["• Hôpital :", appointment.hospital.name],
            ["• Médecin :", f"Dr. {appointment.doctor.name}"],
            ["• Type échographie :", ultrasound_type_display],
            ["• Date confirmée :", date_formatted],
            ["• Heure confirmée :", time_formatted]
        ]
        appointment_table = Table(appointment_data, colWidths=[60*mm, 100*mm])
        appointment_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(appointment_table)
        story.append(Spacer(1, 5))
        
        # Informations importantes avec heure sélectionnée bien visible
        story.append(Paragraph("INFORMATIONS IMPORTANTES :", header_style))
        
        # Vérification que appointment_date existe
        appointment_date_display = "À confirmer"
        if appointment.appointment_date:
            appointment_date_display = appointment.appointment_date.strftime("%d/%m/%Y")
        
        date_info = [
            ["🎯 POSITION DANS LA FILE :", f"{appointment.daily_sequence}"],
            ["💰 MONTANT À PAYER :", appointment.get_formatted_price()],
        ]
        date_table = Table(date_info, colWidths=[70*mm, 90*mm])
        date_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#e8f4fd'), colors.white, colors.HexColor('#e8f4fd'), colors.white]),
        ]))
        story.append(date_table)
        story.append(Spacer(1, 5))
        
        # Note importante sur l'heure
        story.append(Paragraph("💡 IMPORTANT :", header_style))
        time_note = Paragraph(
            f"Vous avez sélectionné le créneau de <b>{time_formatted}</b>. "
            "Merci de respecter cette heure pour le bon fonctionnement de notre service.",
            normal_style
        )
        story.append(time_note)
        story.append(Spacer(1, 5))
        
        # Instructions importantes
        story.append(Paragraph("📋 PROCÉDURE À SUIVRE :", header_style))
        instructions = [
            "• Présentez ce reçu à l'accueil de l'hôpital",
            f"• Arrivez 15 minutes avant {time_formatted} (votre heure de rendez-vous)",
            "• Effectuez le paiement de " + appointment.get_formatted_price() + " à l'accueil",
            "• Apportez votre carte d'identité et ce reçu",
            "• En cas d'empêchement, contactez-nous 48h à l'avance au +257 67338851"
        ]
        
        for instruction in instructions:
            story.append(Paragraph(instruction, normal_style))
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 5))
        
        # Section contact
        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=normal_style,
            fontSize=10,
            textColor=colors.HexColor('#6c757d'),
            alignment=1
        )
        
        story.append(Paragraph("<hr/>", normal_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("📧 Email : contact@mapli.ci", contact_style))
        # Pied de page
        story.append(Spacer(1, 15))
        story.append(Paragraph("<hr/>", normal_style))
        generated_time = datetime.now().strftime("%d/%m/%Y à %H:%M")
        footer_style = ParagraphStyle(
            'Footer',
            parent=normal_style,
            fontSize=8,
            textColor=colors.gray,
            alignment=1
        )
        story.append(Paragraph(f"Reçu généré le {generated_time}", footer_style))
        
        # Génération du PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        print(f"❌ Erreur génération PDF: {str(e)}")
        # PDF d'erreur de secours
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.drawString(100, 750, "Erreur de génération du reçu")
        p.drawString(100, 730, f"Contactez le support: {str(e)}")
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content

def get_pdf_response(appointment, filename=None):
    """Retourne une réponse HTTP avec le PDF"""
    if not filename:
        filename = f"recu_echographie_{appointment.registration_number}.pdf"
    
    pdf_content = generate_appointment_receipt(appointment)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response