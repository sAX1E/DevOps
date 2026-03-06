FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 
RUN pip install pytest

COPY app/*.py ./
COPY app/templates/ ./templates/
COPY app/static/ ./static/

RUN mkdir -p data

EXPOSE 5000

CMD ["python","-c", "from app import app; app.run(host='0.0.0.0', port=5000, debug=True)"]

