from dataclasses import dataclass

@dataclass
class Cookie:
    name: str
    value: str
    
    def __init__(self, name, value, **kwargs):
        self.name = name
        self.value = value

@dataclass
class VCCEntry:
    token_name: str
    token_last_four: str
    token_reference_id: str
    token_created_timestamp: str
    token_updated_timestamp: str
    formatted_token_expiration_date: str
    token_status: str
    card_reference_id: str

    def __init__(self, **kwargs):
        self.token_name = kwargs["tokenName"]
        self.token_last_four = kwargs["tokenLastFour"]
        self.token_reference_id = kwargs["tokenReferenceId"]
        self.token_created_timestamp = kwargs["tokenCreatedTimestamp"]
        self.token_updated_timestamp = kwargs["tokenUpdatedTimestamp"]
        self.formatted_token_expiration_date = kwargs["formattedTokenExpirationDate"]
        self.token_status = kwargs["tokenStatus"]
        self.card_reference_id = kwargs["cardReferenceId"]
