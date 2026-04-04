"""
Pharmacogenomics database for genetic compatibility checking.
Based on PharmGKB, FDA pharmacogenomic biomarkers, and CPIC guidelines.
"""

from typing import Dict, Any, List

# Pharmacogenomics Database - Based on FDA Table of Pharmacogenomic Biomarkers
# https://www.fda.gov/drugs/science-and-research-drugs/table-pharmacogenomic-biomarkers-drug-labeling

PHARMACOGENOMIC_MARKERS = {
    # CYP2C19 - Affects clopidogrel, PPIs, antidepressants
    "clopidogrel": {
        "gene": "CYP2C19",
        "fda_required": True,
        "phenotypes": {
            "poor_metabolizer": {
                "alleles": ["*2/*2", "*2/*3", "*3/*3"],
                "impact": "Reduced conversion to active drug",
                "recommendation": "Consider alternative antiplatelet (ticagrelor, prasugrel)",
                "risk": "HIGH - Increased risk of cardiovascular events",
                "evidence_level": "Level A (Strong)"
            },
            "intermediate_metabolizer": {
                "alleles": ["*1/*2", "*1/*3", "*2/*17"],
                "impact": "Moderately reduced conversion",
                "recommendation": "Consider higher dose or alternative agent",
                "risk": "MODERATE",
                "evidence_level": "Level A"
            },
            "normal_metabolizer": {
                "alleles": ["*1/*1"],
                "impact": "Normal drug response",
                "recommendation": "Standard dosing",
                "risk": "LOW",
                "evidence_level": "Level A"
            },
            "ultrarapid_metabolizer": {
                "alleles": ["*1/*17", "*17/*17"],
                "impact": "Increased conversion to active drug",
                "recommendation": "Standard dosing, may have enhanced effect",
                "risk": "LOW",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "CPIC Guideline for CYP2C19 and Clopidogrel Therapy"
    },
    
    # CYP2D6 - Affects codeine, tamoxifen, many antidepressants
    "codeine": {
        "gene": "CYP2D6",
        "fda_required": True,
        "phenotypes": {
            "poor_metabolizer": {
                "alleles": ["*4/*4", "*4/*5", "*5/*5"],
                "impact": "Little to no conversion to morphine (active form)",
                "recommendation": "Use alternative analgesic (not codeine-related)",
                "risk": "HIGH - No analgesia",
                "evidence_level": "Level A"
            },
            "ultrarapid_metabolizer": {
                "alleles": ["*1/*1xN", "*2/*2xN"],
                "impact": "Rapid conversion to morphine, toxic levels",
                "recommendation": "AVOID codeine - use alternative analgesic",
                "risk": "HIGH - Severe toxicity, respiratory depression, death",
                "evidence_level": "Level A"
            },
            "normal_metabolizer": {
                "alleles": ["*1/*1", "*1/*2"],
                "impact": "Normal conversion",
                "recommendation": "Standard dosing",
                "risk": "LOW",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "CPIC Guideline for CYP2D6 and Codeine Therapy"
    },
    
    # TPMT - Affects thiopurines (azathioprine, mercaptopurine)
    "azathioprine": {
        "gene": "TPMT",
        "fda_required": True,
        "phenotypes": {
            "poor_metabolizer": {
                "alleles": ["*3A/*3A", "*2/*3A"],
                "impact": "Severe myelosuppression risk",
                "recommendation": "Reduce dose by 90% or use alternative",
                "risk": "CRITICAL - Life-threatening myelosuppression",
                "evidence_level": "Level A"
            },
            "intermediate_metabolizer": {
                "alleles": ["*1/*3A", "*1/*2"],
                "impact": "Increased myelosuppression risk",
                "recommendation": "Reduce dose by 30-50%",
                "risk": "HIGH",
                "evidence_level": "Level A"
            },
            "normal_metabolizer": {
                "alleles": ["*1/*1"],
                "impact": "Normal metabolism",
                "recommendation": "Standard dosing with monitoring",
                "risk": "MODERATE",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "CPIC Guideline for TPMT and Thiopurine Therapy"
    },
    
    # SLCO1B1 - Affects statins (simvastatin)
    "simvastatin": {
        "gene": "SLCO1B1",
        "fda_required": True,
        "phenotypes": {
            "poor_function": {
                "alleles": ["*5/*5", "*5/*15"],
                "impact": "Increased statin levels, myopathy risk",
                "recommendation": "Lower dose (≤20mg) or alternative statin (pravastatin, rosuvastatin)",
                "risk": "HIGH - Myopathy, rhabdomyolysis",
                "evidence_level": "Level A"
            },
            "decreased_function": {
                "alleles": ["*1/*5", "*1/*15"],
                "impact": "Moderately increased levels",
                "recommendation": "Standard dose with monitoring, or lower dose",
                "risk": "MODERATE",
                "evidence_level": "Level A"
            },
            "normal_function": {
                "alleles": ["*1/*1"],
                "impact": "Normal statin levels",
                "recommendation": "Standard dosing",
                "risk": "LOW",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "CPIC Guideline for SLCO1B1 and Simvastatin Therapy"
    },
    
    # G6PD - Affects antimalarials, sulfonamides
    "rasburicase": {
        "gene": "G6PD",
        "fda_required": True,
        "phenotypes": {
            "deficient": {
                "impact": "Hemolytic anemia risk",
                "recommendation": "CONTRAINDICATED - do not use",
                "risk": "CRITICAL - Severe hemolysis",
                "evidence_level": "Level A"
            },
            "normal": {
                "impact": "No increased risk",
                "recommendation": "Standard use",
                "risk": "LOW",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "FDA Drug Label"
    },
    
    # HLA-B - Affects allopurinol, carbamazepine, abacavir
    "abacavir": {
        "gene": "HLA-B",
        "fda_required": True,
        "phenotypes": {
            "HLA-B*57:01_positive": {
                "impact": "Hypersensitivity reaction (HSR)",
                "recommendation": "CONTRAINDICATED - do not prescribe",
                "risk": "CRITICAL - Life-threatening HSR in 50-55% of carriers",
                "evidence_level": "Level A"
            },
            "HLA-B*57:01_negative": {
                "impact": "Very low HSR risk (<5%)",
                "recommendation": "Standard use",
                "risk": "LOW",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "CPIC Guideline for HLA-B and Abacavir Therapy"
    },
    
    # Warfarin - CYP2C9 and VKORC1
    "warfarin": {
        "genes": ["CYP2C9", "VKORC1"],
        "fda_required": True,
        "phenotypes": {
            "CYP2C9_poor_metabolizer": {
                "alleles": ["*2/*3", "*3/*3"],
                "impact": "Decreased warfarin metabolism, increased bleeding risk",
                "recommendation": "Reduce initial dose by 50-75%",
                "risk": "HIGH",
                "evidence_level": "Level A"
            },
            "VKORC1_high_sensitivity": {
                "alleles": ["-1639G/A", "-1639A/A"],
                "impact": "Increased warfarin sensitivity",
                "recommendation": "Reduce initial dose by 25-50%",
                "risk": "MODERATE-HIGH",
                "evidence_level": "Level A"
            }
        },
        "guidelines": "CPIC Guideline for Warfarin Dosing",
        "dosing_algorithm": "https://www.warfarindosing.org/"
    }
}


async def check_genetic_compatibility(
    drug: str,
    genetic_markers: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Check pharmacogenomics database for drug-gene interactions.
    Based on FDA Table of Pharmacogenomic Biomarkers and CPIC guidelines.
    """
    drug_lower = drug.lower().strip()
    genetic_markers = genetic_markers or {}
    
    # Check if drug has pharmacogenomic considerations
    if drug_lower not in PHARMACOGENOMIC_MARKERS:
        return {
            "drug": drug,
            "pgx_relevant": False,
            "genetic_markers_checked": genetic_markers,
            "findings": [],
            "summary": f"No FDA-required or CPIC pharmacogenomic testing for {drug}",
            "recommendation": "Standard dosing based on clinical parameters",
            "source": "FDA Table of Pharmacogenomic Biomarkers"
        }
    
    pgx_data = PHARMACOGENOMIC_MARKERS[drug_lower]
    findings = []
    highest_risk = "LOW"
    recommendations = []
    
    # Check if patient has relevant genetic data
    relevant_gene = pgx_data.get("gene") or pgx_data.get("genes", [])[0]
    
    if not genetic_markers:
        return {
            "drug": drug,
            "pgx_relevant": True,
            "fda_required": pgx_data.get("fda_required", False),
            "relevant_gene": relevant_gene,
            "genetic_markers_checked": {},
            "findings": ["No genetic data provided for patient"],
            "summary": f"⚠️ {drug.title()} has FDA pharmacogenomic labeling for {relevant_gene}",
            "recommendation": f"RECOMMENDATION: Test {relevant_gene} before prescribing {drug}",
            "guidelines": pgx_data.get("guidelines"),
            "source": "FDA + CPIC Guidelines"
        }
    
    # Analyze patient's genetic markers
    phenotypes = pgx_data.get("phenotypes", {})
    
    for phenotype_name, phenotype_data in phenotypes.items():
        # Check if patient's genotype matches this phenotype
        patient_genotype = genetic_markers.get(relevant_gene, {}).get("genotype")
        patient_phenotype = genetic_markers.get(relevant_gene, {}).get("phenotype", "").lower().replace(" ", "_")
        
        if patient_phenotype == phenotype_name:
            finding = {
                "gene": relevant_gene,
                "phenotype": phenotype_name.replace("_", " ").title(),
                "impact": phenotype_data.get("impact"),
                "recommendation": phenotype_data.get("recommendation"),
                "risk_level": phenotype_data.get("risk"),
                "evidence": phenotype_data.get("evidence_level")
            }
            findings.append(finding)
            recommendations.append(phenotype_data.get("recommendation"))
            
            # Track highest risk level
            risk = phenotype_data.get("risk", "LOW")
            if "CRITICAL" in risk or "HIGH" in risk:
                highest_risk = risk
    
    # Generate summary
    if findings:
        summary = f"🧬 Genetic testing results for {drug.title()} and {relevant_gene}: {findings[0]['phenotype']}"
    else:
        summary = f"Genetic marker {relevant_gene} data incomplete or not matching known phenotypes"
    
    return {
        "drug": drug,
        "pgx_relevant": True,
        "fda_required": pgx_data.get("fda_required", False),
        "relevant_gene": relevant_gene,
        "genetic_markers_checked": genetic_markers,
        "findings": findings,
        "highest_risk_level": highest_risk,
        "recommendations": recommendations,
        "summary": summary,
        "guidelines": pgx_data.get("guidelines"),
        "source": "FDA Pharmacogenomic Biomarkers + CPIC Guidelines"
    }
