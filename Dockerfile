FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY web/ web/
COPY chat.py web_ui.py ./

RUN pip install --no-cache-dir -e .
RUN mkdir -p logs

EXPOSE 8000 8501

CMD ["python", "-m", "src", "server"]
