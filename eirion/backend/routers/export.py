import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from fpdf import FPDF
from auth import get_current_user
import json

router = APIRouter()

class ExportRequest(BaseModel):
    analysis_payload: dict

class PDFReport(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(15, 23, 42) # blue-gray-900
        self.cell(0, 10, 'EIRION CLINICAL REPORT', border=False, ln=True, align='C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 116, 139) # blue-gray-500
        self.cell(0, 10, 'Personalized Metabolic & Longevity Analysis', border=False, ln=True, align='C')
        self.ln(10)

    def footer(self):
        # Default footer
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

@router.post("/clinician-report")
async def generate_clinician_pdf(request: ExportRequest, user: dict = Depends(get_current_user)):
    """
    Generates a professional 3-page PDF outlining the user's biomarkers, 
    pharmacogenomics, and recommended longevity stack for their physician.
    """
    try:
        data = request.analysis_payload
        
        pdf = PDFReport()
        pdf.add_page()
        
        # 1. Executive Summary
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, 'Patient Profile & Biomarkers', ln=True)
        pdf.set_font('helvetica', '', 11)
        pdf.set_text_color(51, 65, 85)
        
        score = data.get("risk_summary", {}).get("risk_level", "Unknown")
        bio_age = data.get("biological_age", "N/A")
        
        pdf.cell(0, 8, f'Computed Biological Age: {bio_age}', ln=True)
        pdf.cell(0, 8, f'Risk Stratification: {score.upper()}', ln=True)
        pdf.ln(5)

        # 2. Recommendations
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, 'Recommended Interventions', ln=True)
        
        for rec in data.get("recommendations", []):
            pdf.set_font('helvetica', 'B', 11)
            pdf.set_text_color(2, 132, 199) # light blue
            pdf.cell(0, 8, f"Action: {rec['title']}", ln=True)
            
            pdf.set_font('helvetica', '', 10)
            pdf.set_text_color(71, 85, 105)
            # Use multi_cell for wrapping text
            pdf.multi_cell(0, 6, rec['details'])
            pdf.ln(2)
            
            if rec.get('evidence_refs'):
                pdf.set_font('helvetica', 'I', 9)
                refs = ", ".join(rec['evidence_refs'])
                pdf.multi_cell(0, 5, f"Literature: {refs}")
            
            pdf.ln(4)

        # Output bytes
        pdf_bytes = pdf.output(dest='S')
        
        return Response(
            content=pdf_bytes, 
            media_type="application/pdf", 
            headers={"Content-Disposition": "attachment; filename=Eirion_Clinical_Report.pdf"}
        )

    except Exception as e:
        print(f"[Export] PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate clinical report.")
