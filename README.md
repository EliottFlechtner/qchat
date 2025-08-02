# qchat

A post-quantum chat server built with FastAPI and PostgreSQL.

## 🟢 How to Launch Everything

From your project root:

```bash
docker compose up --build
```

To rebuild without cache:

```bash
docker compose up --build --force-recreate
```

To run detached:

```bash
docker compose up -d
```

---

## 🟢 How to Connect to the Services

### ➤ FastAPI backend

* **In browser or API client**: [http://localhost:8000](http://localhost:8000)
* **Swagger docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### ➤ PostgreSQL

From your host machine:

```bash
psql -h localhost -U admin -d qchatdb
```

Password will be `admin` as per `.env`.

Or from inside the container:

```bash
docker exec -it db psql -U admin -d qchatdb
```

Now features CI/CD!