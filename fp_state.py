"""
File: fp_state.py
Handles state management for Financial Planning functionality
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class FPReportState:
    """State management for FP report sections"""
    samenvatting: Dict = field(default_factory=lambda: {
        "netto_besteedbaar_inkomen": None,
        "hoofdpunten": [],
        "kernadvies": None
    })
    
    uitwerking_advies: Dict = field(default_factory=lambda: {
        "content": None,
        "graphs": None
    })
    
    huidige_situatie: Dict = field(default_factory=lambda: {
        "content": None,
        "graphs": None
    })
    
    situatie_later: Dict = field(default_factory=lambda: {
        "voor_advies": None,
        "na_advies": None,
        "graphs": None
    })
    
    situatie_overlijden: Dict = field(default_factory=lambda: {
        "voor_advies": None,
        "na_advies": None,
        "graphs": None
    })
    
    situatie_arbeidsongeschiktheid: Dict = field(default_factory=lambda: {
        "voor_advies": None,
        "na_advies": None,
        "graphs": None
    })
    
    erven_schenken: Dict = field(default_factory=dict)
    
    actiepunten: Dict = field(default_factory=lambda: {
        "client": [],
        "veldhuis": []
    })
    
    sections_complete: Dict = field(default_factory=lambda: {
        "samenvatting": False,
        "uitwerking_advies": False,
        "huidige_situatie": False,
        "situatie_later": False,
        "situatie_overlijden": False,
        "situatie_arbeidsongeschiktheid": False,
        "erven_schenken": False,
        "actiepunten": False
    })

    def update_section(self, section: str, content: Dict) -> None:
        """Update content for a specific section"""
        if hasattr(self, section):
            setattr(self, section, content)
            self.sections_complete[section] = True

    def is_complete(self) -> bool:
        """Check if all sections are complete"""
        return all(self.sections_complete.values())

    def get_progress(self) -> float:
        """Get progress percentage"""
        completed = sum(1 for x in self.sections_complete.values() if x)
        total = len(self.sections_complete)
        return (completed / total) * 100 if total > 0 else 0