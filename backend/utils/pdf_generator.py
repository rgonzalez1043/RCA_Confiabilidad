"""Reporte paginado: texto escapado, herramientas de análisis y cierre verificable."""
from datetime import datetime
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def generar_reporte_rca(rca_data: dict, output_path: str):
    styles = getSampleStyleSheet()
    elements = []
    def paragraph(text, style='BodyText'):
        elements.append(Paragraph(escape(str(text)).replace('\n', '<br/>'), styles[style]))
    paragraph(f"REPORTE RCA - {rca_data.get('codigo', 'N/A')}", 'Heading1')
    for section, fields in [
        ('Identificación', [('titulo','Título'), ('estado','Estado'), ('criticidad','Criticidad'),
            ('fecha_evento','Fecha del evento'), ('area','Área'), ('planta','Planta'), ('equipo','Equipo'),
            ('descripcion_falla','Descripción de la falla'), ('impacto','Impacto'),
            ('tiempo_parada_horas','Horas de parada'), ('costo_estimado','Costo estimado')]),
        ('Análisis', [('causa_inmediata','Causa inmediata'), ('causa_raiz','Causa raíz'),
            ('causas_contribuyentes','Causas contribuyentes'), ('aprobado_por','Aprobado por'),
            ('fecha_aprobacion','Fecha de aprobación')]),
        ('Implementación', [('acciones_correctivas','Acciones correctivas'),
            ('acciones_preventivas','Acciones preventivas'), ('responsable','Responsable'),
            ('fecha_compromiso','Fecha compromiso')]),
        ('Verificación', [('verificacion_efectividad','Resultado de efectividad'),
            ('fecha_verificacion','Fecha de verificación'), ('efectivo','Acciones efectivas'),
            ('fecha_cierre','Fecha de cierre')]),
    ]:
        paragraph(section, 'Heading2')
        for field, label in fields:
            value = rca_data.get(field)
            if value is not None and value != '':
                paragraph(label, 'Heading4')
                paragraph(('Sí' if value else 'No') if isinstance(value, bool) else value)
    whys = rca_data.get('cinco_porques') or []
    if any(whys):
        paragraph('5 Porqués', 'Heading2')
        for level, why in enumerate(whys, 1):
            paragraph(f'{level}. {why or "Sin respuesta"}')
    if rca_data.get('ishikawa'):
        paragraph('Diagrama de Ishikawa', 'Heading2')
        for category, causes in rca_data['ishikawa'].items():
            paragraph(category, 'Heading4')
            for cause in causes:
                paragraph(cause)
    elements.append(Spacer(1, 16))
    paragraph(f'Reporte generado: {datetime.now():%Y-%m-%d %H:%M:%S}', 'Italic')
    SimpleDocTemplate(output_path, pagesize=A4).build(elements)
    return output_path