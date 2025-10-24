"""
Utilidad para generar reportes PDF de RCAs
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import datetime
import os

def generar_reporte_rca(rca_data: dict, output_path: str):
    """
    Genera un PDF con el reporte completo de un RCA
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado
    titulo_style = ParagraphStyle(
        'TituloRCA',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=12
    )
    
    # Título
    titulo = Paragraph(f"REPORTE RCA - {rca_data.get('codigo', 'N/A')}", titulo_style)
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información general
    info_data = [
        ['Título:', rca_data.get('titulo', 'N/A')],
        ['Fecha Evento:', str(rca_data.get('fecha_evento', 'N/A'))],
        ['Área:', rca_data.get('area', 'N/A')],
        ['Equipo:', rca_data.get('equipo', 'N/A')],
        ['Criticidad:', rca_data.get('criticidad', 'N/A')],
        ['Estado:', rca_data.get('estado', 'N/A')],
        ['Responsable:', rca_data.get('responsable', 'N/A')],
    ]
    
    tabla_info = Table(info_data, colWidths=[2*inch, 4*inch])
    tabla_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Descripción de falla
    if rca_data.get('descripcion_falla'):
        elementos.append(Paragraph("<b>Descripción de la Falla:</b>", styles['Heading2']))
        elementos.append(Paragraph(rca_data['descripcion_falla'], styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Causa raíz
    if rca_data.get('causa_raiz'):
        elementos.append(Paragraph("<b>Causa Raíz:</b>", styles['Heading2']))
        elementos.append(Paragraph(rca_data['causa_raiz'], styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Acciones correctivas
    if rca_data.get('acciones_correctivas'):
        elementos.append(Paragraph("<b>Acciones Correctivas:</b>", styles['Heading2']))
        elementos.append(Paragraph(rca_data['acciones_correctivas'], styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Pie de página
    elementos.append(Spacer(1, 0.5*inch))
    fecha_generacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elementos.append(Paragraph(f"<i>Reporte generado: {fecha_generacion}</i>", styles['Italic']))
    
    # Generar PDF
    doc.build(elementos)
    return output_path