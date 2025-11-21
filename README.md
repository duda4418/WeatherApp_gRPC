# WeatherApp_gRPC

A modern Python application providing weather data via gRPC and REST APIs, with MongoDB persistence and a simple UI. Built for reliability, testability, and easy extension.

## Features
- **gRPC API** for fast, typed weather queries
- **REST API** (FastAPI) for browser and HTTP clients
- **MongoDB** for storing weather observations
- **OpenWeatherMap** integration
- **Comprehensive unit and integration tests**
- **Docker Compose** for local MongoDB
- **Simple UI** for charting weather data

## Project Structure
```
weather_server.py           # Entrypoint for gRPC server
main.py                     # Entrypoint for REST API/UI
client.py                   # Example gRPC client
core/                       # Configuration and settings
weather_service/            # gRPC service logic and providers
UI/                         # REST API, services, and static files
proto/                      # Protobuf definitions and generated code
scripts/                    # Utilities for proto generation and data ingest
db/                         # MongoDB repository
mongo_db/                   # Docker Compose and init scripts
```

## Quick Start
1. **Clone the repo**
   ```sh
   git clone https://github.com/duda4418/WeatherApp_gRPC.git
   cd WeatherApp_gRPC
   ```
2. **Install dependencies**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
   - Copy `.env.example` to `.env` and fill in your OpenWeather API key, Mongo URI, etc.
4. **Start MongoDB (optional, for persistence)**
   ```sh
   cd mongo_db
   docker-compose up -d
   ```
5. **Run the gRPC server**
   ```sh
   python weather_server.py
   ```
6. **Run the REST API/UI**
   ```sh
   python main.py
   ```

## Testing
- **Unit tests:**
  ```sh
  pytest tests/unit
  ```
- **Integration tests:**
  ```sh
  pytest tests/integration
  ```
- **Coverage report:**
  ```sh
  pytest --cov=weather_service --cov=db --cov=core --cov-report=term-missing tests
  ```

## Protobuf
- Edit `proto/weather.proto` as needed.
- Regenerate Python code:
  ```sh
  python scripts/generate_proto.py
  ```

## Contributing
- Fork and clone the repo
- Create a feature branch
- Write tests for new features
- Submit a pull request

## License
MIT

## Maintainer
- [duda4418](https://github.com/duda4418)

---

