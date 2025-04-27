

# VideoSummarizer

VideoSummarizer is a powerful application that automatically generates concise summaries of YouTube videos using AI. It extracts key points, insights, and information, saving you time while ensuring you don't miss important content.

## 🌟 Features

- **AI-Powered Summaries**: Generate comprehensive summaries of YouTube videos using Google's Gemini AI
- **Multi-Language Support**: Summarize videos in multiple languages
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-Time Processing**: Asynchronous processing with Kafka for efficient handling of summary requests
- **Docker Integration**: Easy deployment with containerized services

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key
- YouTube API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/video-summarizer.git
   cd video-summarizer
   ```

2. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

3. Update the `.env` file with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   YOUTUBE_API_KEY=your_youtube_api_key_here
   ```

4. Start the application:
   ```bash
   docker-compose up -d
   ```

5. Access the application at [http://localhost](http://localhost)

## 🏗️ Architecture

VideoSummarizer uses a microservices architecture with the following components:

- **Frontend**: React application with TypeScript and Vite
- **Backend**: FastAPI service that processes video URLs and generates summaries
- **Kafka**: Message broker for asynchronous processing of summary requests
- **Zookeeper**: Required for Kafka operation

<!-- ![Architecture Diagram](docs/images/architecture.png) -->

## 💻 Development

### Local Development Setup

1. Start the backend services:
   ```bash
   docker-compose up -d zookeeper kafka backend
   ```

2. Install frontend dependencies and start the development server:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. The frontend will be available at [http://localhost:5173](http://localhost:5173)

### Project Structure

```
video-summarizer/
├── backend/                # FastAPI backend service
│   ├── app/                # Application code
│   ├── Dockerfile          # Backend container configuration
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── public/             # Static assets
│   ├── src/                # Source code
│   ├── Dockerfile          # Frontend container configuration
│   └── package.json        # Node.js dependencies
├── docker-compose.yml      # Docker Compose configuration
└── .env                    # Environment variables
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📚 API Documentation

When the backend is running, API documentation is available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🔧 Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description |
|----------|-------------|
| API_BASE_URL | Base URL for API endpoints |
| GOOGLE_API_KEY | Google Gemini API key for AI summaries |
| YOUTUBE_API_KEY | YouTube API key for video metadata |
| KAFKA_BOOTSTRAP_SERVERS | Kafka server addresses |
| LOG_LEVEL | Logging level (INFO, DEBUG, etc.) |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Google Gemini AI](https://ai.google.dev/) for providing the AI summarization capabilities
- [YouTube API](https://developers.google.com/youtube/v3) for video metadata retrieval
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework
- [Kafka](https://kafka.apache.org/) for message processing