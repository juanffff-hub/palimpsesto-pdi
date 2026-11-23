# Palimpsesto en Hugging Face Spaces (plan gratuito, CPU). Lo arma scripts/deploy_hf.py.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OMP_NUM_THREADS=2

RUN apt-get update \
 && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Spaces ejecuta el contenedor con el usuario 1000.
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt waitress==3.0.2

COPY --chown=user . .
USER user

# Los pesos v0.4.0 se descargan de la release de GitHub y se verifican por SHA-256 al construir la imagen.
RUN python -c "from pathlib import Path; from palimpsesto.weights import ensure_models; ensure_models(Path('models'))" \
 && rm -rf models/.download_cache

ENV PALIMPSESTO_PUBLIC_HOST=0.0.0.0 \
    PALIMPSESTO_PUBLIC_PORT=7860 \
    PALIMPSESTO_TRUSTED_PROXY=* \
    PALIMPSESTO_EMBEDDED=1

EXPOSE 7860
CMD ["python", "-u", "run_public.py"]
