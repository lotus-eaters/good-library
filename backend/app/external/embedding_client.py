import asyncio
from functools import partial

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

_model = None


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _model


async def embed(text: str) -> list[float]:
    return (await embed_batch([text]))[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    cleaned = [t.replace("\n", " ").strip() for t in texts]
    loop = asyncio.get_event_loop()
    model = _get_model()
    vectors = await loop.run_in_executor(
        None, partial(list, model.embed(cleaned))
    )
    return [v.tolist() for v in vectors]
