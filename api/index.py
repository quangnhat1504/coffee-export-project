"""Vercel serverless entrypoint for the Flask app."""

from app import create_app


app = create_app()
