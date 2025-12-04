FROM ubuntu
USER ubuntu

CMD ["uvicorn", "--host", "0.0.0.0", "main:app"]