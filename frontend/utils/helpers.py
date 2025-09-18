def mask_email(email):
    """Masks an email address for display purposes."""
    if not email or '@' not in email:
        return ""
    parts, domain = email.split('@', 1)
    if len(parts) == 0:
        return f"***@{domain}"
    if len(parts) <= 3:
        return f"{parts[0]}***@{domain}"
    return f"{parts[:2]}***{parts[-1]}@{domain}"