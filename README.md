# QChat - Post-Quantum Secure Chat Application

Development status: active work has historically happened on `dev`, while `main` tracks integrated merges.

A secure, end-to-end encrypted chat application built with post-quantum cryptography using FastAPI, PostgreSQL, and the Open Quantum Safe (liboqs) library.

## 🔐 Features

- **Post-Quantum Cryptography**: Uses quantum-resistant algorithms for key exchange and digital signatures
- **End-to-End Encryption**: Messages are encrypted with AES-256 using post-quantum key encapsulation
- **Real-time Communication**: WebSocket-based messaging for instant communication
- **Secure Authentication**: Post-quantum digital signatures for user authentication
- **Dockerized Deployment**: Easy deployment with Docker Compose

## 🏗️ Architecture

- **Backend**: FastAPI server with WebSocket support
- **Database**: PostgreSQL for user and message storage
- **Client**: Python CLI chat client
- **Cryptography**: liboqs (Open Quantum Safe) library
- **Reverse Proxy**: Nginx for production deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/EliottFlechtner/qchat.git
cd qchat
```

### 2. Environment Setup

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
POSTGRES_DB=qchatdb
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Application Configuration
DEBUG=true
SECRET_KEY=your-secret-key-here
```

### 3. Launch the Application

#### Using Docker Compose (Recommended)

Start all services:
```bash
docker compose up --build
```

To run in detached mode:
```bash
docker compose up -d --build
```

To rebuild without cache:
```bash
docker compose up --build --force-recreate
```

#### Local Development (Alternative)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start PostgreSQL (ensure it's running on localhost:5432)

3. Update `.env` to point to your local database

4. Run the server:
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 Accessing the Services

### FastAPI Backend
- **Main API**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### PostgreSQL Database
From your host machine:
```bash
psql -h localhost -p 5432 -U admin -d qchatdb
```

From inside the Docker container:
```bash
docker exec -it db psql -U admin -d qchatdb
```

### Nginx (Production)
- **Frontend**: [http://localhost:80](http://localhost:80)

## 💬 Using the Chat Client

### Start a Chat Session

1. Ensure the server is running (see Launch section above)

2. Run the client from the project root:
```bash
python -m client.main <your_username> <recipient_username>
```

Example:
```bash
python -m client.main alice bob
```

### Chat Commands

- Type messages and press Enter to send
- Use `Ctrl+C` to exit the chat
- Messages are automatically encrypted with post-quantum cryptography

### Multiple Users

To simulate a conversation, open multiple terminals and run different user sessions:

Terminal 1 (Alice):
```bash
python -m client.main alice bob
```

Terminal 2 (Bob):
```bash
python -m client.main bob alice
```

## 🔧 Development

### Project Structure

```
qchat/
├── client/                 # Chat client application
│   ├── main.py            # Client entry point
│   ├── api.py             # API communication
│   ├── crypto/            # Cryptographic modules
│   ├── network/           # WebSocket handling
│   ├── services/          # Core client services
│   └── utils/             # Helper utilities
├── server/                # FastAPI server
│   ├── main.py            # Server entry point
│   ├── db/                # Database models and connection
│   ├── routes/            # HTTP and WebSocket routes
│   └── utils/             # Server utilities
├── shared/                # Shared models and types
├── liboqs-python/         # Post-quantum cryptography library
├── frontend/              # Web frontend (if applicable)
├── tests/                 # Test suites
├── docker-compose.yml     # Docker services configuration
├── Dockerfile             # Application container
├── nginx.conf             # Nginx configuration
└── requirements.txt       # Python dependencies
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/test_crypto.py

# Run with coverage
python -m pytest --cov=client --cov=server tests/
```

### Development Database Access

To reset the database:
```bash
docker compose down -v
docker compose up --build
```

To backup the database:
```bash
docker exec -t db pg_dump -U admin qchatdb > backup.sql
```

## 🔒 Security Features

- **Post-Quantum Key Exchange**: Uses quantum-resistant KEM algorithms
- **Digital Signatures**: Post-quantum signature schemes for authentication
- **AES-256 Encryption**: Industry-standard symmetric encryption
- **Perfect Forward Secrecy**: New keys for each session
- **No Plaintext Storage**: Messages are stored encrypted

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 5432, and 80 are available
2. **Docker permission issues**: Run with `sudo` if needed
3. **Database connection errors**: Wait for PostgreSQL health check to pass
4. **Client connection issues**: Verify the server is running and accessible

### Logs

View application logs:
```bash
docker compose logs -f app
```

View database logs:
```bash
docker compose logs -f db
```

View all logs:
```bash
docker compose logs -f
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Open Quantum Safe](https://openquantumsafe.org/) for the liboqs library
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [PostgreSQL](https://www.postgresql.org/) for the database
