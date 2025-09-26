# src/auth/application/commands/create_user_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    password: str
