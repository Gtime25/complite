# CompLite - SOX & ESG Compliance Tool

A comprehensive compliance management tool supporting both SOX and ESG frameworks with AI-powered insights, anomaly detection, and automated reporting.

![CompLite Dashboard](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)

## 🚀 Features

- **Multi-Framework Support**: SOX and ESG compliance management
- **AI-Powered Insights**: OpenAI GPT-4 integration for intelligent analysis
- **Anomaly Detection**: Automated detection of compliance issues
- **Real-Time Alerts**: Slack integration for immediate notifications
- **PDF Reports**: Comprehensive compliance reports with charts
- **Analytics Dashboard**: Performance metrics and trend analysis
- **User Authentication**: Secure JWT-based authentication
- **File Upload**: Support for CSV and Excel files

## 🛠️ Tech Stack

- **Frontend**: React.js with Bootstrap
- **Backend**: FastAPI (Python)
- **AI**: OpenAI GPT-4
- **Database**: ChromaDB (vector database)
- **Charts**: Matplotlib & Recharts
- **Authentication**: JWT tokens
- **File Processing**: Pandas

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- OpenAI API key

### Backend Setup

```bash
cd soxlite-backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd soxlite-frontend
npm install
```

### Environment Variables

Create a `.env` file in the `soxlite-backend` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
JWT_SECRET=your_jwt_secret_here
```

## 🚀 Running the Application

### Development Mode

1. **Start Backend:**
   ```bash
   cd soxlite-backend
   uvicorn main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd soxlite-frontend
   npm start
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📊 Sample Data

The project includes sample datasets for testing:

- `soxlite-backend/datasets/complex_sox_sample.csv` - SOX compliance data
- `soxlite-backend/datasets/complex_esg_sample.csv` - ESG compliance data

## 🔧 API Endpoints

### Authentication
- `POST /signup` - User registration
- `POST /login` - User login
- `GET /verify-token` - Token verification

### File Operations
- `POST /auto-embed/` - Upload and embed files
- `POST /detect-anomalies/` - Detect compliance anomalies
- `POST /detect-alerts/` - Generate real-time alerts

### AI Operations
- `POST /query/` - Query with memory
- `POST /ask-ai/` - AI-powered analysis with PDF generation

### Analytics
- `POST /analytics/trends/` - Trend analysis
- `POST /analytics/owner-performance/` - Owner performance
- `POST /analytics/benchmarks/` - Benchmark analysis
- `POST /analytics/heatmap/` - Heatmap generation

## 🌐 Deployment

### Railway (Recommended)

1. **Fork this repository**
2. **Connect to Railway**
3. **Set environment variables**
4. **Deploy automatically**

### Render

1. **Create Web Service** for backend
2. **Create Static Site** for frontend
3. **Configure build commands**
4. **Deploy**

### Heroku

1. **Add Procfile** (already included)
2. **Set environment variables**
3. **Deploy via Git**

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📁 Project Structure

```
soxlite/
├── soxlite-backend/          # FastAPI backend
│   ├── main.py              # Main application
│   ├── ai_insights.py       # AI analysis functions
│   ├── datasets/            # Sample datasets
│   └── uploads/             # File uploads (gitignored)
├── soxlite-frontend/        # React frontend
│   ├── src/
│   │   ├── App.js           # Main app component
│   │   ├── HomePage.js      # Landing page
│   │   ├── LoginPage.js     # Authentication
│   │   ├── UploadPage.js    # File upload interface
│   │   └── styles.css       # Styling
│   └── public/
├── requirements.txt         # Python dependencies
├── Procfile                # Heroku configuration
└── README.md               # This file
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the API docs at `/docs`
- **Questions**: Open a discussion

## 🙏 Acknowledgments

- OpenAI for GPT-4 integration
- FastAPI for the excellent web framework
- React team for the frontend framework
- ChromaDB for vector database capabilities

---

**Made with ❤️ for compliance professionals** 