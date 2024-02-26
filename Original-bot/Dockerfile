FROM python
WORKDIR /app

RUN pip install --upgrade pip

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python3"]
CMD ["app.py"]