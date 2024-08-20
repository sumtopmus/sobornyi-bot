from urllib.parse import urlparse


providers = {
    'google': 'Google',
    'facebook': 'Facebook',
    'fb': 'Facebook',
}


def provider(url: str) -> str:
    domain = urlparse(url).netloc
    domain_noext = domain.split('.')[-2]
    if domain_noext in providers:
        return providers[domain_noext]
    return domain


