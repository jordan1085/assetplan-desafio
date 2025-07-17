FROM python:3.13

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc

COPY . /app

RUN python -m pip install --upgrade pip && \
    pip install .

EXPOSE 8020

CMD ["chroma-mcp"]
