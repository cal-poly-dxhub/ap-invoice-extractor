# Invoice Processing System

AI-powered invoice processing application that extracts structured data from PDF invoices using Amazon Bedrock models and provides real-time chat analysis.

## Features

- PDF invoice upload and processing
- Multi-page document support
- Intelligent text extraction with Nova Lite and Claude 3.5 Sonnet fallback
- Structured data extraction (vendor, amounts, line items, dates)
- Real-time chat interface for invoice analysis
- PDF preview with zoom and navigation
- Session-based document management
- Semantic search across uploaded documents

## Tech Stack

**Frontend**
- React with Tailwind CSS
- react-pdf for document viewing
- Real-time chat interface

**Backend**
- FastAPI Python server
- Amazon Bedrock (Nova Lite, Claude 3.5 Sonnet, Claude Haiku)
- Amazon S3 for document storage
- In-memory vector search with embeddings
- PyPDF2 for text extraction

**Deployment**
- AWS Elastic Beanstalk
- S3 static hosting for frontend

## Architecture

The system uses a hybrid AI approach - Nova Lite for cost-effective processing with Claude 3.5 Sonnet fallback for complex legal documents. All document data is stored with session isolation for multi-tenancy.
