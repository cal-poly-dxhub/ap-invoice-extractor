# INVOICEABLE
## AI-Powered Invoice Processing System

## Table of Contents

- [Collaboration](#collaboration)
- [Disclaimers](#disclaimers)
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deployment](#deployment)
- [Contributors](#contributors)
- [Support](#support)

# Collaboration

Thanks for your interest in our solution. Having specific examples of replication and usage allows us to continue to grow and scale our work. If you clone or use this repository, kindly shoot us a quick email to let us know you are interested in this work!

<wwps-cic@amazon.com>

# Disclaimers

**Customers are responsible for making their own independent assessment of the information in this document.**

**This document:**

(a) is for informational purposes only,

(b) represents current AWS product offerings and practices, which are subject to change without notice, and

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided "as is" without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

(d) is not to be considered a recommendation or viewpoint of AWS

**Additionally, all prototype code and associated assets should be considered:**

(a) as-is and without warranties

(b) not suitable for production environments

(c) to include shortcuts in order to support rapid prototyping such as, but not limited to, relaxed authentication and authorization and a lack of strict adherence to security best practices

**All work produced is open source. More information can be found in the GitHub repo.**

## Overview

**INVOICEABLE** is an AI-powered invoice processing application that automates manual invoice handling. Developed during the DxHub AI CSU Summer Camp, it extracts raw data from PDF invoices using a Python library, then leverages an AI model to structure the data and generate GL-ready Excel or CSV files for export. The application also includes a chatbot that allows users to ask questions about the invoices uploaded in the current session.

### Key Features

- **Multi-format Support**: Process PDF, TXT, JSON, CSV, and MD files
- **AI-Powered Extraction**: Uses Amazon Nova Lite / Claude 3.5 Sonnet for optimal cost and accuracy
- **Real-time Chat Interface**: Natural language queries about processed invoices
- **Session Management**: Secure, isolated processing sessions
- **Export Capabilities**: GL-ready Excel/CSV exports for accounting systems
- **Interactive PDF Preview**: Multiple view modes with zoom and navigation
- **Batch Processing**: Handle multiple invoices simultaneously

## Architecture

The solution consists of several key components:

1. **Frontend Interface**
   - React 18 application with Tailwind CSS
   - Interactive PDF viewer with react-pdf
   - Real-time chat interface for document analysis
   - Responsive design for desktop and mobile

2. **API Layer**
   - FastAPI Python server with high-performance REST endpoints
   - Session-based architecture with automatic cleanup
   - CORS enabled for cross-origin requests

3. **AI Services**
   - Amazon Bedrock with Nova Lite for primary text extraction
   - Claude 3.5 Sonnet for complex document fallback
   - Claude 3 Haiku for conversational chat responses
   - Amazon Titan for vector embeddings and semantic search

4. **Data Storage and Management**
   - Amazon S3 for secure document storage
   - File-based local storage for development
   - PyPDF2 for local text extraction
   - Pickle-based document persistence


## Prerequisites

- AWS CLI configured with appropriate permissions
- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)
- Request model access for the required models through AWS console in Bedrock (Amazon Nova Lite, Claude 3.5 Sonnet V2, Claude 3 Haiku, Amazon Titan Text V2)

## Initial Setup

1. **Enable Bedrock Model Access:**
   - Navigate to the AWS Bedrock console
   - Request access to all models from both Anthropic and Amazon
   - Ensure you're working in the correct AWS region for your deployment

2. **Configure AWS credentials**
   ```bash
   aws configure
   ```
   You'll be prompted to enter:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region name (us-west-2 recommended)
   - Default output format

## Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/cal-poly-dxhub/ap-invoice-extractor.git
   cd ap-invoice-extractor
   ```

2. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start the backend server**
   ```bash
   python api_server.py
   ```

5. **Start the frontend (in a new terminal)**
   ```bash
   cd frontend
   npm start
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs


## Contributors

This project was developed by talented students during the **DxHub AI CSU Summer Camp**:

**Students:**
- **Noah Gallego** 
- **Harpreet Kaur**
- **Carlos De Orta**
- **Elizsa Montoya**
- **Emanuel Gonzalez**

**Mentor:**
- **Shrey Shah** - <sshah84@calpoly.edu>

## Support

For any queries or issues, please contact:

- Darren Kraker - <dkraker@amazon.com>
- Shrey Shah, Jr. SDE - <sshah84@calpoly.edu>
