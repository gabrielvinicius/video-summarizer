# src/summarization/application/commands/process_summary_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessSummaryCommand:
    transcription_id: str
    provider: str
