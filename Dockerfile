FROM python:3.11

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
COPY ./packages.txt /app/packages.txt

RUN apt-get update && xargs -r -a /app/packages.txt apt-get install -y && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir -r /app/requirements.txt

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user
ENV PATH=$HOME/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

EXPOSE 8501

CMD streamlit run app.py \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.fileWatcherType none
