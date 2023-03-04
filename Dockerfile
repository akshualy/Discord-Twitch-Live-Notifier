FROM python:3.11.2

COPY /poetry.lock /poetry.lock
COPY /pyproject.toml /pyproject.toml
COPY ./app /app

WORKDIR /
RUN apt-get update
RUN apt-get -y dist-upgrade
RUN apt-get -y install python3-pip curl
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH=/root/.local/bin:$PATH
RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "-m" , "app.main"]
