import pytest
from src.transcription.application.transcription_service import TranscriptionService


@pytest.mark.asyncio
async def test_transcribe_returns_text_from_audio():
    service = TranscriptionService()
    file_path = "tests/assets/sample_audio.mp4"  # certifique-se de que esse arquivo existe

    result = await service.transcribe(file_path)

    assert isinstance(result, str)
    assert "esperado" in result.lower()  # dependa do conteúdo do áudio
