# tests/infrastructure/test_speech_recognition.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np
import asyncio
from src.transcription.infrastructure.speech_recognition import WhisperTranscriber


@pytest.mark.asyncio
async def test_whisper_transcribe_success():
    """Testa transcrição bem-sucedida com áudio válido"""
    # Setup
    mock_model = MagicMock()
    mock_decode = MagicMock()
    mock_decode.text = "Hello world"
    mock_model.decode.return_value = mock_decode

    with patch('whisper.load_model', return_value=mock_model):
        transcriber = WhisperTranscriber("base")
        transcriber._decode_audio_bytes = AsyncMock(
            return_value=np.array([0.1, 0.2, -0.1], dtype=np.float32)
        )

        # Execute
        result = await transcriber.transcribe(b"audio_data")

        # Validate
        assert result == "Hello world"
        transcriber._decode_audio_bytes.assert_awaited_once_with(b"audio_data")


@pytest.mark.asyncio
async def test_whisper_transcribe_empty_audio():
    """Testa comportamento com áudio vazio"""
    transcriber = WhisperTranscriber("base")
    transcriber._decode_audio_bytes = AsyncMock(return_value=np.array([], dtype=np.float32))

    result = await transcriber.transcribe(b"")

    assert result == "" or result is None


@pytest.mark.asyncio
async def test_whisper_decode_audio_failure():
    """Testa falha na decodificação do áudio"""
    transcriber = WhisperTranscriber("base")
    transcriber._decode_audio_bytes = AsyncMock(
        side_effect=RuntimeError("FFmpeg error")
    )

    with pytest.raises(RuntimeError) as excinfo:
        await transcriber.transcribe(b"invalid")

    assert "FFmpeg error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_whisper_transcription_failure():
    """Testa falha durante a transcrição"""
    mock_model = MagicMock()
    mock_model.decode.side_effect = RuntimeError("Model failure")

    with patch('whisper.load_model', return_value=mock_model):
        transcriber = WhisperTranscriber("base")
        transcriber._decode_audio_bytes = AsyncMock(
            return_value=np.array([0.1, 0.2], dtype=np.float32)
        )

        with pytest.raises(RuntimeError) as excinfo:
            await transcriber.transcribe(b"valid_audio")

        assert "Model failure" in str(excinfo.value)


# Teste de Integração (requer FFmpeg instalado)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_whisper_real_transcription():
    """Teste de integração com arquivo de áudio real"""
    # Gera um arquivo WAV simples (1 segundo de silêncio)
    sample_rate = 16000
    audio_data = np.zeros(sample_rate, dtype=np.float32)
    wav_bytes = (b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
                 b'\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00')

    transcriber = WhisperTranscriber("tiny")  # Modelo pequeno para velocidade

    # Execute
    result = await transcriber.transcribe(wav_bytes)

    # Validate
    assert isinstance(result, str)
    assert len(result) >= 0  # Pode ser string vazia para silêncio