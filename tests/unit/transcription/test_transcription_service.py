# tests/application/test_transcription_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.transcription.application.transcription_service import TranscriptionService
from src.transcription.domain.transcription import Transcription, TranscriptionStatus
from src.video_management.domain.video import Video, VideoStatus
from src.shared.events.event_bus import EventBus
from src.storage.application.storage_service import StorageService


@pytest.fixture
def service_mocks():
    """Configura mocks para dependências do serviço"""
    return {
        "speech_recognition": AsyncMock(),
        "storage_service": AsyncMock(),
        "event_bus": AsyncMock(),
        "transcription_repo": AsyncMock(),
        "video_repo": AsyncMock(),
    }


@pytest.fixture
def transcription_service(service_mocks):
    return TranscriptionService(**service_mocks)


@pytest.mark.asyncio
async def test_process_new_transcription_success(transcription_service, service_mocks):
    """Testa fluxo bem-sucedido para nova transcrição"""
    # Setup
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")
    transcription = Transcription(id="trans1", video_id=video_id, status=TranscriptionStatus.PROCESSING)

    service_mocks["video_repo"].find_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = None
    service_mocks["transcription_repo"].save.return_value = transcription
    service_mocks["storage_service"].download.return_value = b"audio_data"
    service_mocks["speech_recognition"].transcribe.return_value = "Transcribed text"

    # Execute
    result = await transcription_service.process_transcription(video_id)

    # Validate
    assert result.status == TranscriptionStatus.COMPLETED
    assert result.text == "Transcribed text"

    # Verify state transitions
    assert video.status == VideoStatus.COMPLETED
    assert video.transcription_id == "trans1"

    # Verify calls
    service_mocks["video_repo"].save.assert_awaited()
    service_mocks["transcription_repo"].save.assert_awaited()
    service_mocks["event_bus"].publish.assert_awaited_once_with(
        "transcription_completed",
        {"video_id": video_id, "transcription_id": "trans1"}
    )


@pytest.mark.asyncio
async def test_idempotency_existing_transcription(transcription_service, service_mocks):
    """Testa idempotência quando transcrição já existe"""
    video_id = "vid1"
    existing_transcription = Transcription(
        id="trans1",
        video_id=video_id,
        status=TranscriptionStatus.COMPLETED,
        text="Existing text"
    )
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")

    service_mocks["video_repo"].find_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = existing_transcription

    # Execute
    result = await transcription_service.process_transcription(video_id)

    # Validate
    assert result == existing_transcription

    # Verify no processing happened
    service_mocks["storage_service"].download.assert_not_awaited()
    service_mocks["speech_recognition"].transcribe.assert_not_awaited()
    service_mocks["video_repo"].save.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_failed_video(transcription_service, service_mocks):
    """Testa reprocessamento de vídeo com falha anterior"""
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.FAILED, file_path="audio.mp3")
    failed_transcription = Transcription(
        id="trans1",
        video_id=video_id,
        status=TranscriptionStatus.FAILED,
        failure_reason="Previous error"
    )

    service_mocks["video_repo"].find_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = failed_transcription
    service_mocks["storage_service"].download.return_value = b"audio_data"
    service_mocks["speech_recognition"].transcribe.return_value = "Success text"

    # Execute
    result = await transcription_service.process_transcription(video_id)

    # Validate
    assert result.status == TranscriptionStatus.COMPLETED
    assert result.text == "Success text"
    assert result.failure_reason is None
    assert video.status == VideoStatus.COMPLETED


@pytest.mark.asyncio
async def test_audio_download_failure(transcription_service, service_mocks):
    """Testa tratamento de falha no download do áudio"""
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")

    service_mocks["video_repo"].find_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = None
    service_mocks["storage_service"].download.side_effect = Exception("Download failed")

    # Execute & Validate
    with pytest.raises(Exception):
        await transcription_service.process_transcription(video_id)

    # Verify failure states
    assert video.status == VideoStatus.FAILED
    transcription = service_mocks["transcription_repo"].save.call_args[0][0]
    assert transcription.status == TranscriptionStatus.FAILED
    assert "Download failed" in transcription.failure_reason


@pytest.mark.asyncio
async def test_transcription_failure(transcription_service, service_mocks):
    """Testa tratamento de falha na transcrição"""
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")

    service_mocks["video_repo"].find_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = None
    service_mocks["storage_service"].download.return_value = b"audio_data"
    service_mocks["speech_recognition"].transcribe.side_effect = RuntimeError("Transcription failed")

    # Execute & Validate
    with pytest.raises(RuntimeError):
        await transcription_service.process_transcription(video_id)

    # Verify failure states
    assert video.status == VideoStatus.FAILED
    transcription = service_mocks["transcription_repo"].save.call_args[0][0]
    assert transcription.status == TranscriptionStatus.FAILED
    assert "Transcription failed" in transcription.failure_reason


@pytest.mark.asyncio
async def test_event_publishing_failure(transcription_service, service_mocks):
    """Testa que falha na publicação de evento não quebra o fluxo"""
    video_id = "vid1"
    video = Video(id=video_id, status=VideoStatus.UPLOADED, file_path="audio.mp3")

    service_mocks["video_repo"].find_by_id.return_value = video
    service_mocks["transcription_repo"].find_by_video_id.return_value = None
    service_mocks["storage_service"].download.return_value = b"audio_data"
    service_mocks["speech_recognition"].transcribe.return_value = "Text"
    service_mocks["event_bus"].publish.side_effect = Exception("Event failed")

    # Execute
    result = await transcription_service.process_transcription(video_id)

    # Validate main flow succeeded
    assert result.status == TranscriptionStatus.COMPLETED
    assert video.status == VideoStatus.COMPLETED

    # Verify error was logged but not propagated
    service_mocks["event_bus"].publish.assert_awaited()


# Teste de Integração Completo
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_transcription_flow():
    """Teste de integração completa com dependências reais"""
    from src.shared.events.in_memory_event_bus import InMemoryEventBus
    from src.storage.infrastructure.in_memory_storage import InMemoryStorage
    from src.transcription.infrastructure.in_memory_transcription_repository import InMemoryTranscriptionRepository
    from src.video_management.infrastructure.in_memory_video_repository import InMemoryVideoRepository

    # Configurar dependências reais
    video_repo = InMemoryVideoRepository()
    transcription_repo = InMemoryTranscriptionRepository()
    storage = InMemoryStorage()
    event_bus = InMemoryEventBus()

    # Criar transcriber real (usando modelo tiny para velocidade)
    speech_recognition = WhisperTranscriber("tiny")

    service = TranscriptionService(
        speech_recognition=speech_recognition,
        storage_service=storage,
        event_bus=event_bus,
        transcription_repository=transcription_repo,
        video_repository=video_repo
    )

    # Criar e salvar vídeo
    video = Video(
        id="test_video",
        file_path="test_audio.wav",
        status=VideoStatus.UPLOADED
    )
    await video_repo.save(video)

    # Criar arquivo de áudio de teste (1 segundo de silêncio)
    sample_rate = 16000
    audio_data = np.zeros(sample_rate, dtype=np.float32)
    wav_bytes = (b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
                 b'\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00')

    # Fazer upload do áudio
    await storage.upload("test_audio.wav", wav_bytes)

    # Executar processamento
    result = await service.process_transcription("test_video")

    # Validar resultados
    assert result.status == TranscriptionStatus.COMPLETED
    assert isinstance(result.text, str)

    # Validar estado do vídeo
    updated_video = await video_repo.find_by_id("test_video")
    assert updated_video.status == VideoStatus.COMPLETED
    assert updated_video.transcription_id == result.id

    # Validar evento publicado
    events = event_bus.get_events("transcription_completed")
    assert len(events) == 1
    assert events[0]["video_id"] == "test_video"
    assert events[0]["transcription_id"] == result.id