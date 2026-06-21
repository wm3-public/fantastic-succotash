from pydantic import BaseModel


class SensitiveModel(BaseModel):
    """Since our API deals with sensitive information that we need to manage
    properly for PCI DSS compliance, this model allows us to indicate fields
    that need to be partially or fully redacted before output.
    """

    pass
