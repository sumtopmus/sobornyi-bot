from urllib.parse import urlparse

providers = {
    "google": "Google",
    "facebook": "Facebook",
    "fb": "Facebook",
    "eventbrite": "Eventbrite",
}


def provider(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove 'www.' if present
    if domain.startswith("www."):
        domain = domain[4:]

    # Get the main domain part
    parts = domain.split(".")
    if len(parts) >= 2:
        domain_name = parts[-2]
        return providers.get(domain_name, "Link")

    return "Link"
