"""
Configuration settings for Invoice Processor CDK deployment
"""
import os
import yaml
from pathlib import Path

class Config:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        # AWS Configuration
        aws_config = config_data.get('aws', {})
        self.AWS_REGION = os.environ.get("CDK_DEFAULT_REGION", aws_config.get('region', 'us-west-2'))
        self.AWS_ACCOUNT = os.environ.get("CDK_DEFAULT_ACCOUNT", aws_config.get('account'))
        
        # Stack Configuration
        stack_config = config_data.get('stack', {})
        self.STACK_NAME = stack_config.get('name', 'InvoiceProcessorStack')
        
        # S3 Configuration
        s3_config = config_data.get('s3', {})
        self.S3_INVOICE_BUCKET = s3_config.get('invoice_bucket', 'invoice-processor-documents')
        self.S3_FRONTEND_BUCKET = s3_config.get('frontend_bucket', 'invoice-processor-frontend')
        
        # Bedrock Configuration
        bedrock_config = config_data.get('bedrock', {})
        self.NOVA_LITE_MODEL = bedrock_config.get('nova_lite_model', 'us.amazon.nova-lite-v1:0')
        self.CLAUDE_SONNET_MODEL = bedrock_config.get('claude_sonnet_model', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        self.CLAUDE_HAIKU_MODEL = bedrock_config.get('claude_haiku_model', 'anthropic.claude-3-haiku-20240307-v1:0')
        
        # Lambda Configuration
        lambda_config = config_data.get('lambda', {})
        self.LAMBDA_TIMEOUT = lambda_config.get('timeout', 300)
        self.LAMBDA_MEMORY = lambda_config.get('memory', 1024)
        self.LAMBDA_RUNTIME = lambda_config.get('runtime', 'python3.13')
        
        # API Gateway Configuration
        api_config = config_data.get('api', {})
        self.API_NAME = api_config.get('name', 'InvoiceProcessorAPI')
        cors_config = api_config.get('cors', {})
        self.API_CORS_ALLOW_ORIGINS = cors_config.get('allow_origins', ['*'])
        self.API_CORS_ALLOW_METHODS = cors_config.get('allow_methods', ['GET', 'POST', 'OPTIONS'])
        self.API_CORS_ALLOW_HEADERS = cors_config.get('allow_headers', ['Content-Type', 'Authorization'])
        
        # CloudFront Configuration
        cloudfront_config = config_data.get('cloudfront', {})
        self.CLOUDFRONT_DEFAULT_ROOT_OBJECT = cloudfront_config.get('default_root_object', 'index.html')
        self.CLOUDFRONT_ERROR_RESPONSES = cloudfront_config.get('error_responses', [
            {
                'http_status': 404,
                'response_http_status': 200,
                'response_page_path': '/index.html'
            }
        ])
        
        # Environment-specific overrides
        env = self.get_environment()
        env_config = config_data.get('environments', {}).get(env, {})
        
        if 'cors_origins' in env_config:
            self.API_CORS_ALLOW_ORIGINS = env_config['cors_origins']
        
        # Apply environment suffixes
        env_suffix = env_config.get('s3_suffix', '')
        
        if env_suffix:
            self.S3_INVOICE_BUCKET = f"{self.S3_INVOICE_BUCKET}-{env_suffix}"
            self.S3_FRONTEND_BUCKET = f"{self.S3_FRONTEND_BUCKET}-{env_suffix}"
    
    def get_environment(self):
        return os.environ.get("ENVIRONMENT", "dev")
    
    def is_production(self):
        return self.get_environment().lower() == "prod"
    
    def get_stack_name(self):
        env = self.get_environment()
        return f"{self.STACK_NAME}-{env}" if env != "prod" else self.STACK_NAME
    
    def get_s3_bucket_name(self, bucket_type='invoice'):
        """Get S3 bucket name with account and region suffix"""
        base_name = self.S3_INVOICE_BUCKET if bucket_type == 'invoice' else self.S3_FRONTEND_BUCKET
        return f"{base_name}-{self.AWS_ACCOUNT}-{self.AWS_REGION}"

def get_config():
    """Get configuration instance"""
    return Config()