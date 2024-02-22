FROM python
WORKDIR /app
RUN pip install --upgrade pip
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8443

ENTRYPOINT ["python3"]

CMD ["app.py"]
