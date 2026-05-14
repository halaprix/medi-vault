#!/usr/bin/env python3
"""Seed biomarker reference data — idempotent (ON CONFLICT DO NOTHING)."""
import asyncio
from sqlalchemy import text
from app.core.database import async_session
from app.models import Biomarker, BiomarkerCategory

BIOMARKERS = [
    # ── Lipid Panel ──
    ("2093-3", "Cholesterol, Total", "Total Cholesterol", "lipid_panel", "mmol/L", "Main cholesterol measure", ["Cholesterol total","TC","Chol"]),
    ("2085-9", "Cholesterol in LDL", "LDL Cholesterol", "lipid_panel", "mmol/L", "Low-density lipoprotein", ["LDL","LDL-C","bad cholesterol"]),
    ("2086-7", "Cholesterol in HDL", "HDL Cholesterol", "lipid_panel", "mmol/L", "High-density lipoprotein", ["HDL","HDL-C","good cholesterol"]),
    ("2571-8", "Triglycerides", "Triglycerides", "lipid_panel", "mmol/L", "Fat in blood", ["TG","TRIG","triacylglycerol"]),
    ("13457-7", "Cholesterol in VLDL", "VLDL Cholesterol", "lipid_panel", "mmol/L", "Very low-density lipoprotein", ["VLDL","VLDL-C"]),
    ("43396-1", "non-HDL Cholesterol", "non-HDL Cholesterol", "lipid_panel", "mmol/L", "Total minus HDL", ["non-HDL","nonHDL","Non-HDL-C"]),
    ("9830-5", "LDL/HDL Ratio", "LDL/HDL Ratio", "lipid_panel", "ratio", "LDL to HDL ratio", ["LDL:HDL","LDL HDL ratio"]),

    # ── CMP ──
    ("2345-7", "Glucose", "Glucose", "metabolic_panel", "mmol/L", "Blood sugar", ["GLU","blood sugar","fasting glucose"]),
    ("3094-0", "Urea Nitrogen", "BUN", "metabolic_panel", "mmol/L", "Blood urea nitrogen", ["BUN","Urea","Blood urea"]),
    ("2160-0", "Creatinine", "Creatinine", "metabolic_panel", "umol/L", "Kidney function", ["CREAT","Cr","serum creatinine"]),
    ("33914-3", "eGFR", "eGFR", "metabolic_panel", "mL/min/1.73m2", "Estimated glomerular filtration rate", ["eGFR","GFR","kidney function"]),
    ("2951-2", "Sodium", "Sodium", "metabolic_panel", "mmol/L", "Electrolyte", ["Na","Na+"]),
    ("2823-3", "Potassium", "Potassium", "metabolic_panel", "mmol/L", "Electrolyte", ["K","K+"]),
    ("2075-0", "Chloride", "Chloride", "metabolic_panel", "mmol/L", "Electrolyte", ["Cl","Cl-"]),
    ("2028-9", "Carbon Dioxide", "CO2", "metabolic_panel", "mmol/L", "Bicarbonate", ["CO2","bicarbonate","HCO3"]),
    ("17861-6", "Calcium", "Calcium", "metabolic_panel", "mmol/L", "Bone health", ["Ca","Ca2+"]),
    ("2885-2", "Protein", "Total Protein", "metabolic_panel", "g/L", "Total serum protein", ["TP","serum protein"]),
    ("1751-7", "Albumin", "Albumin", "metabolic_panel", "g/L", "Liver protein", ["ALB"]),
    ("10834-0", "Globulin", "Globulin", "metabolic_panel", "g/L", "Calculated: TP - ALB", ["GLOB"]),
    ("1759-0", "Albumin/Globulin Ratio", "A/G Ratio", "metabolic_panel", "ratio", "Albumin to globulin ratio", ["A/G","AG ratio"]),
    ("1975-2", "Bilirubin.total", "Total Bilirubin", "metabolic_panel", "umol/L", "Liver function", ["TBIL","total bili"]),
    ("1968-7", "Bilirubin.direct", "Direct Bilirubin", "metabolic_panel", "umol/L", "Conjugated bilirubin", ["DBIL","direct bili","conjugated"]),
    ("1742-6", "Alanine aminotransferase", "ALT", "liver", "U/L", "Liver enzyme", ["ALT","SGPT","alanine transaminase"]),
    ("1920-8", "Aspartate aminotransferase", "AST", "liver", "U/L", "Liver enzyme", ["AST","SGOT","aspartate transaminase"]),
    ("6768-6", "Alkaline phosphatase", "ALP", "liver", "U/L", "Liver/bone enzyme", ["ALP","alk phos","alkaline phosphatase"]),

    # ── CBC ──
    ("26453-1", "Erythrocytes", "RBC", "cbc", "10^12/L", "Red blood cell count", ["RBC","red blood cells","erythrocytes"]),
    ("718-7", "Hemoglobin", "Hemoglobin", "cbc", "g/dL", "Oxygen carrier", ["HGB","Hb","haemoglobin"]),
    ("4544-3", "Hematocrit", "Hematocrit", "cbc", "%", "RBC volume fraction", ["HCT","Ht","packed cell volume"]),
    ("30428-7", "MCV", "MCV", "cbc", "fL", "Mean corpuscular volume", ["MCV","mean cell volume"]),
    ("28539-5", "MCH", "MCH", "cbc", "pg", "Mean corpuscular hemoglobin", ["MCH"]),
    ("28542-9", "MCHC", "MCHC", "cbc", "g/dL", "Mean corpuscular hemoglobin concentration", ["MCHC"]),
    ("30385-9", "RDW", "RDW", "cbc", "%", "Red cell distribution width", ["RDW","RDW-CV"]),
    ("26515-7", "Platelets", "Platelets", "cbc", "10^9/L", "Clotting cells", ["PLT","thrombocytes"]),
    ("26464-8", "Leukocytes", "WBC", "cbc", "10^9/L", "White blood cell count", ["WBC","white blood cells","leukocytes"]),
    ("30180-4", "Neutrophils/100 leukocytes", "Neutrophils %", "cbc", "%", "Neutrophil percentage", ["NEUT%","neutrophils percent"]),
    ("30216-6", "Lymphocytes/100 leukocytes", "Lymphocytes %", "cbc", "%", "Lymphocyte percentage", ["LYMPH%","lymphocytes percent"]),
    ("30160-6", "Monocytes/100 leukocytes", "Monocytes %", "cbc", "%", "Monocyte percentage", ["MONO%","monocytes percent"]),
    ("30222-4", "Eosinophils/100 leukocytes", "Eosinophils %", "cbc", "%", "Eosinophil percentage", ["EO%","eosinophils percent"]),
    ("30140-8", "Basophils/100 leukocytes", "Basophils %", "cbc", "%", "Basophil percentage", ["BASO%","basophils percent"]),

    # ── Thyroid ──
    ("3016-3", "Thyrotropin", "TSH", "thyroid", "mIU/L", "Thyroid stimulating hormone", ["TSH","thyrotropin","thyroid"]),
    ("3024-7", "Triiodothyronine (T3)", "Free T3", "thyroid", "pmol/L", "Free triiodothyronine", ["FT3","free T3","triiodothyronine"]),
    ("3020-5", "Thyroxine (T4) free", "Free T4", "thyroid", "pmol/L", "Free thyroxine", ["FT4","free T4","thyroxine"]),
    ("3053-6", "Triiodothyronine total", "Total T3", "thyroid", "nmol/L", "Total T3", ["TT3","total T3"]),
    ("3026-2", "Thyroxine total", "Total T4", "thyroid", "nmol/L", "Total T4", ["TT4","total T4"]),
    ("8099-4", "Thyroperoxidase Ab", "Anti-TPO", "thyroid", "IU/mL", "Thyroid autoantibody", ["Anti-TPO","TPO Ab","thyroid peroxidase"]),

    # ── Vitamins & Minerals ──
    ("1986-9", "25-Hydroxyvitamin D3", "Vitamin D (25-OH)", "vitamins_minerals", "nmol/L", "Vitamin D status", ["Vit D","25-OH D","25-hydroxyvitamin D","vitamin D"]),
    ("2132-9", "Cobalamin (Vitamin B12)", "Vitamin B12", "vitamins_minerals", "pmol/L", "B12 status", ["B12","cobalamin","vitamin B12"]),
    ("2284-8", "Folate", "Folate", "vitamins_minerals", "nmol/L", "Folate status", ["FOL","folic acid","vitamin B9"]),
    ("2498-4", "Iron", "Iron", "vitamins_minerals", "umol/L", "Serum iron", ["Fe","serum iron"]),
    ("2276-4", "Ferritin", "Ferritin", "vitamins_minerals", "ug/L", "Iron storage", ["FERR","iron stores"]),
    ("2500-7", "Iron binding capacity", "TIBC", "vitamins_minerals", "umol/L", "Total iron binding capacity", ["TIBC","total iron binding"]),
    ("2502-3", "Transferrin saturation", "Transferrin Saturation", "vitamins_minerals", "%", "Iron saturation", ["TSAT","% saturation","transferrin sat"]),
    ("19123-9", "Magnesium", "Magnesium", "vitamins_minerals", "mmol/L", "Magnesium level", ["Mg","Mg2+"]),
    ("5763-4", "Zinc", "Zinc", "vitamins_minerals", "umol/L", "Zinc level", ["Zn","Zn2+"]),
    ("5631-3", "Copper", "Copper", "vitamins_minerals", "umol/L", "Copper level", ["Cu","Cu2+"]),

    # ── Hormones ──
    ("2986-8", "Testosterone", "Testosterone Total", "hormones", "nmol/L", "Total testosterone", ["TT","total test","testosterone"]),
    ("2991-8", "Testosterone Free", "Testosterone Free", "hormones", "pmol/L", "Free testosterone", ["FT","free test"]),
    ("2243-4", "Estradiol", "Estradiol", "hormones", "pmol/L", "Estrogen", ["E2","estrogen"]),
    ("2839-9", "Progesterone", "Progesterone", "hormones", "nmol/L", "Progesterone", ["PROG","P4"]),
    ("2191-5", "Dehydroepiandrosterone sulfate", "DHEA-S", "hormones", "umol/L", "Adrenal androgen", ["DHEAS","DHEA-S","DHEA sulfate"]),
    ("2143-6", "Cortisol", "Cortisol", "hormones", "nmol/L", "Stress hormone", ["CORT","stress hormone"]),
    ("2289-7", "Follitropin", "FSH", "hormones", "IU/L", "Follicle stimulating hormone", ["FSH","follitropin"]),
    ("2290-5", "Lutropin", "LH", "hormones", "IU/L", "Luteinizing hormone", ["LH","lutropin"]),
    ("2044-6", "Prolactin", "Prolactin", "hormones", "mIU/L", "Prolactin", ["PRL"]),
    ("2484-4", "Insulin-like growth factor 1", "IGF-1", "hormones", "nmol/L", "Growth factor", ["IGF1","IGF-1","somatomedin C"]),

    # ── Inflammation ──
    ("1988-5", "C Reactive Protein", "CRP", "inflammation", "mg/L", "Inflammation marker", ["CRP","C-reactive protein"]),
    ("30522-7", "High Sensitivity C-Reactive Protein", "hs-CRP", "inflammation", "mg/L", "Cardiac risk marker", ["hsCRP","high sensitivity CRP","cardiac CRP"]),
    ("4537-7", "Erythrocyte sedimentation rate", "ESR", "inflammation", "mm/h", "Inflammation rate", ["ESR","sed rate"]),
    ("3173-2", "Homocysteine", "Homocysteine", "inflammation", "umol/L", "Cardiovascular risk", ["HCY","homocystine"]),
    ("3255-7", "Fibrinogen", "Fibrinogen", "inflammation", "g/L", "Clotting factor", ["FIB","fibrinogen antigen"]),

    # ── Diabetes ──
    ("4548-4", "Hemoglobin A1c", "HbA1c", "diabetes", "%", "3-month average glucose", ["HbA1c","A1c","glycated hemoglobin","glycohemoglobin"]),
    ("20448-7", "Insulin", "Insulin (fasting)", "diabetes", "uIU/mL", "Fasting insulin", ["INS","fasting insulin","serum insulin"]),
    ("93692-5", "HOMA-IR", "HOMA-IR", "diabetes", "index", "Insulin resistance index", ["HOMA-IR","HOMA","insulin resistance"]),

    # ── Kidney ──
    ("3084-1", "Urate", "Uric Acid", "kidney", "umol/L", "Uric acid level", ["UA","uric acid","urate"]),
    ("33863-2", "Cystatin C", "Cystatin C", "kidney", "mg/L", "Kidney function marker", ["CYSC","cystatin"]),
    ("9318-7", "Microalbumin/Creatinine Ratio", "Microalbumin/Creatinine Ratio", "kidney", "mg/mmol", "Urine albumin ratio", ["ACR","albumin:creatinine","microalbumin"]),
]

UNIT_CONVERSIONS = [
    ("2093-3", "mg/dL", "mmol/L", 0.02586),
    ("2085-9", "mg/dL", "mmol/L", 0.02586),
    ("2086-7", "mg/dL", "mmol/L", 0.02586),
    ("2571-8", "mg/dL", "mmol/L", 0.01129),
    ("2345-7", "mg/dL", "mmol/L", 0.05551),
    ("2160-0", "mg/dL", "umol/L", 88.42),
    ("2498-4", "ug/dL", "umol/L", 0.1791),
    ("2500-7", "ug/dL", "umol/L", 0.1791),
]


async def seed():
    async with async_session() as session:
        for (loinc, std_name, disp_name, cat, unit, desc, aliases) in BIOMARKERS:
            await session.execute(
                text("""
                    INSERT INTO biomarkers (loinc_code, standard_name, display_name, category, standard_unit, description, aliases)
                    VALUES (:loinc, :std_name, :disp_name, :cat, :unit, :desc, :aliases)
                    ON CONFLICT (loinc_code) DO NOTHING
                """),
                {
                    "loinc": loinc, "std_name": std_name, "disp_name": disp_name,
                    "cat": cat, "unit": unit, "desc": desc, "aliases": aliases,
                }
            )
        await session.commit()
        result = await session.execute(text("SELECT COUNT(*) FROM biomarkers"))
        count = result.scalar()
        print(f"✅ Seeded {count} biomarkers")


if __name__ == "__main__":
    asyncio.run(seed())
