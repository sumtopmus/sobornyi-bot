from urllib.parse import urlparse


providers = {
    "google": "Google",
    "facebook": "Facebook",
    "fb": "Facebook",
}


def provider(url: str) -> str:
    domain = urlparse(url).netloc
    domain_noext = domain.split(".")[-2]
    return providers.get(domain_noext, "Link")
