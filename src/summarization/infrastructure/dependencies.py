from src.summarization.infrastructure.interfaces import ISummarizer


async def get_summarizer() -> 'ISummarizer':
    from src.summarization.infrastructure.huggingface_summarizer import HuggingFaceSummarizer
    return HuggingFaceSummarizer()
