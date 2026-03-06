FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pytest

<<<<<<< HEAD
COPY app/*.py ./
COPY templates/ ./templates/
COPY static/ ./static/
=======
# Копируем всё содержимое папки app в /app
COPY app/ .
>>>>>>> dev

RUN mkdir -p data

EXPOSE 5000

# Запускаем app.py напрямую
CMD ["python", "app.py"]
