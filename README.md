# Socioscope-notebook

A FastHTML application for analyzing and discussing transcripts using RAG (Retrieval-Augmented Generation) powered by Groq.

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
3. Groq API key (get one at https://console.groq.com)

### Environment Variables

Configure these environment variables in your Vercel project settings:

- `MONGODB_URI` - MongoDB connection string
- `AUTH_ID` - Authentication username
- `AUTH_SECRET` - Authentication password
- `GROQ_API_KEY` - API key for Groq service

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
