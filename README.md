# Socioscope-notebook

A FastHTML application for analyzing and discussing transcripts using RAG (Retrieval-Augmented Generation).

## Local Development

### Install
```shell
pip install -r requirements.txt
```

### Run
```shell
python main.py
```

## Vercel Deployment

### Prerequisites
1. A Vercel account
2. MongoDB Atlas account (or other MongoDB instance)
3. RAG API endpoint configured

### Environment Variables
Configure these environment variables in your Vercel project settings:

- `MONGODB_URI` - MongoDB connection string
- `AUTH_ID` - Authentication username
- `AUTH_SECRET` - Authentication password
- `RAG_API_ENDPOINT` - API endpoint for the RAG service
- `RAG_API_KEY` - API key for RAG service
- `RAG_API_SECRET` - API secret for RAG service

### Deploy to Vercel

1. Push this repository to GitHub
2. Import the project in Vercel
3. Configure the environment variables
4. Deploy

Or use the Vercel CLI:
```shell
vercel
```

### Important Notes
- The app uses an in-memory SQLite database for session state, which resets on each deployment
- Consider using a persistent database solution for production use
