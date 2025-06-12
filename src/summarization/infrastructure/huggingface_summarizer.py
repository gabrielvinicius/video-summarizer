from transformers import pipeline, AutoTokenizer
import torch
import asyncio
from threading import Lock


class HuggingFaceSummarizer:
    def __init__(self, model_name="google-t5/t5-base"):
        """
        Inicializa o sumarizador com detecção automática de dispositivo.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Comprimentos máximos baseados no modelo
        self.model_max_length = getattr(self.tokenizer, 'model_max_length', 1024)
        self.max_input_length = min(self.model_max_length, 512)  # Melhor desempenho com mais contexto
        self.max_summary_length = 64
        self.min_summary_length = 16

        # Pipeline de sumarização com detecção automática de dispositivo
        self.summarizer = pipeline(
            "summarization",
            model=model_name,
            tokenizer=self.tokenizer,
            framework="pt",
            device=-1
        )

        # Dispositivo detectado automaticamente
        self.device = self.summarizer.device
        print(f"HuggingFaceSummarizer inicializado. Dispositivo selecionado automaticamente: {self.device}")

        self.lock = Lock()

    def empty_device_cache(self):
        """Libera a memória não utilizada do dispositivo, se aplicável."""
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()
        elif self.device.type == 'xpu':
            torch.xpu.empty_cache()

    def split_text_into_chunks(self, text: str) -> list[str]:
        """Divide o texto em chunks baseados em tokens"""
        if not text.strip():
            return []

        tokens = self.tokenizer.tokenize(text)
        chunks = [
            tokens[i:i + self.max_input_length]
            for i in range(0, len(tokens), self.max_input_length)
        ]

        return [
            self.tokenizer.convert_tokens_to_string(chunk)
            for chunk in chunks
        ]

    async def summarize(self, text: str) -> str:
        """Processa o texto em chunks e retorna o resumo concatenado"""
        if not text.strip():
            return ""

        # Limpa o cache do dispositivo antes de iniciar
        self.empty_device_cache()

        print(self.summarizer(text, max_length=130, min_length=30, do_sample=False))

        chunks = self.split_text_into_chunks(text)
        summaries = []

        for chunk in chunks:
            summary = await self._summarize_chunk(chunk)
            summaries.append(summary)

        self.empty_device_cache()

        return " ".join(summaries)

    async def _summarize_chunk(self, chunk: str) -> str:
        """Processa um chunk individual com tratamento de erro robusto"""
        with self.lock:
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(
                    None,
                    lambda: self.summarizer(
                        chunk,
                        max_length=self.max_summary_length,
                        min_length=self.min_summary_length,
                        do_sample=False,
                        num_beams=4,
                        truncation=True,
                        no_repeat_ngram_size=3
                    )[0]['summary_text']
                )
            except Exception as e:
                print(f"Erro ao sumarizar chunk: {str(e)}")
                return ""
