FROM python:3.12

RUN pip install --upgrade poetry

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . /app

RUN poetry install

ENTRYPOINT ["pphsd"]