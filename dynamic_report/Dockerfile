FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 
COPY dynamic_report.py /app/scripts/
RUN chmod +x /app/scripts/*.py
CMD [ "python", "/app/scripts/dynamic_report.py" ]
