from enum import Enum

class CalloutForm(str, Enum):
    """Axis 1 — Call-outs & special blocks."""
    C_WARNING = "C-WARNING"   # Boxed warnings, black-box safety notices
    C_QUOTE   = "C-QUOTE"     # Quotes, epigraphs
    C_CODE    = "C-CODE"      # Code/snippet blocks
