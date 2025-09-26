# src/auth/application/commands/authenticate_user_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class AuthenticateUserCommand:
    email: str
    password: str
