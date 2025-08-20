import logging
# Configure logging
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def normalize_crop_name(crop_name: str) -> str:
    """Normalize crop name for consistent usage"""
    if not crop_name:
        return ""

    # Convert to lowercase and strip whitespace
    normalized = crop_name.lower().strip()

    # Handle common variations
    variations = {
        "गेहूं": "wheat",
        "चावल": "rice",
        "धान": "rice",
        "टमाटर": "tomato",
        "प्याज": "onion",
        "आलू": "potato",
        "गन्ना": "sugarcane",
        "कपास": "cotton",
        "सोयाबीन": "soybean",
        "मक्का": "maize",
        "बाजरा": "bajra"
    }

    return variations.get(normalized, normalized)