FROM python:3.12-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 EDR_HOST=0.0.0.0 EDR_DATA_DIR=/app/var/server
WORKDIR /app
COPY requirements/server.lock /app/requirements/server.lock
RUN pip install --no-cache-dir -r requirements/server.lock && useradd --uid 10001 --create-home behedr
COPY backend /app/backend
COPY rules /app/rules
COPY manage.py /app/manage.py
RUN mkdir -p /app/var/server && chown -R behedr:behedr /app/var
USER behedr
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/ready', timeout=3)"
CMD ["python", "manage.py", "serve"]
