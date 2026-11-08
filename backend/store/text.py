import re


def new_uzbek_alphabet(value):
    """Render Uzbek text with the custom letters shown in the supplied alphabet."""
    text = str(value or "")
    text = re.sub(r"(?i)o['’‘ʻ]", lambda m: "Ö" if m.group(0)[0].isupper() else "ö", text)
    text = re.sub(r"(?i)g['’‘ʻ]", lambda m: "Ğ" if m.group(0)[0].isupper() else "ğ", text)
    text = re.sub(r"(?i)sh", lambda m: "Ş" if m.group(0)[0].isupper() else "ş", text)
    text = re.sub(r"(?i)ch", lambda m: "Ç" if m.group(0)[0].isupper() else "ç", text)
    return text
