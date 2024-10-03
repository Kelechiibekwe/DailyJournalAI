FROM postgres

# Install dependencies and pgvector
RUN apt-get update && apt-get install -y postgresql-server-dev-all build-essential git \
    && git clone https://github.com/pgvector/pgvector.git \
    && cd pgvector && make && make install \
    && rm -rf /pgvector