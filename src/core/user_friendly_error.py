from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class UserFriendlyError:
    """Data describing an error in a user-friendly way."""

    cause: str
    user_message: str
    suggestions: List[str] = field(default_factory=list)
    documentation_link: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "cause": self.cause,
            "message": self.user_message,
            "suggestions": self.suggestions,
            "documentation_link": self.documentation_link,
        }
