from aws_cdk import (
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from config import get_config

class InvoiceProcessorStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Load configuration
        self.config = get_config()

        # S3 Bucket for invoice documents and metadata
        invoice_bucket = s3.Bucket(
            self, "InvoiceBucket",
            bucket_name=self.config.get_s3_bucket_name('invoice'),
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldSessions",
                    enabled=True,
                    expiration=Duration.days(7)  # Auto-delete after 7 days
                )
            ]
        )

        # IAM Role for Lambda
        lambda_role = iam.Role(
            self, "InvoiceProcessorLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                invoice_bucket.bucket_arn,
                                f"{invoice_bucket.bucket_arn}/*"
                            ]
                        )
                    ]
                ),
                "BedrockAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Lambda Layer for Python dependencies
        python_deps_layer = lambda_.LayerVersion(
            self, "PythonDepsLayer",
            code=lambda_.Code.from_asset("lambda-layers/python-deps", bundling={
                "image": lambda_.Runtime.PYTHON_3_9.bundling_image,
                "command": [
                    "bash", "-c",
                    "pip install -r requirements.txt -t /asset-output/python"
                ]
            }),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
            description="Python dependencies for invoice processing"
        )
        
        # Lambda function for invoice processing
        invoice_lambda = lambda_.Function(
            self, "InvoiceProcessorLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            architecture=lambda_.Architecture.X86_64,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(self.config.LAMBDA_TIMEOUT),
            memory_size=self.config.LAMBDA_MEMORY,
            role=lambda_role,
            layers=[python_deps_layer],
            environment={
                "S3_BUCKET_NAME": invoice_bucket.bucket_name,
                "NOVA_LITE_MODEL": self.config.NOVA_LITE_MODEL,
                "CLAUDE_SONNET_MODEL": self.config.CLAUDE_SONNET_MODEL,
                "CLAUDE_HAIKU_MODEL": self.config.CLAUDE_HAIKU_MODEL
            }
        )

        # API Gateway
        api = apigateway.RestApi(
            self, "InvoiceProcessorApi",
            rest_api_name=self.config.API_NAME,
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=self.config.API_CORS_ALLOW_ORIGINS,
                allow_methods=self.config.API_CORS_ALLOW_METHODS,
                allow_headers=self.config.API_CORS_ALLOW_HEADERS
            )
        )

        # Grant API Gateway permission to invoke Lambda
        invoice_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"{api.arn_for_execute_api()}/*/*"
        )
        
        # Lambda integration
        lambda_integration = apigateway.LambdaIntegration(invoice_lambda)
        
        # API Gateway resources and methods
        # /process-document
        process_resource = api.root.add_resource("process-document")
        process_resource.add_method("POST", lambda_integration)
        
        # /update-document
        update_resource = api.root.add_resource("update-document")
        update_resource.add_method("POST", lambda_integration)
        
        # /chat
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method("POST", lambda_integration)
        
        # /session/{sessionId}/delete
        session_resource = api.root.add_resource("session")
        session_id_resource = session_resource.add_resource("{sessionId}")
        delete_resource = session_id_resource.add_resource("delete")
        delete_resource.add_method("DELETE", lambda_integration)

        # Frontend S3 bucket
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=self.config.get_s3_bucket_name('frontend'),
            removal_policy=RemovalPolicy.DESTROY,
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # CloudFront distribution
        error_responses = []
        for error_config in self.config.CLOUDFRONT_ERROR_RESPONSES:
            error_responses.append(
                cloudfront.ErrorResponse(
                    http_status=error_config['http_status'],
                    response_http_status=error_config['response_http_status'],
                    response_page_path=error_config['response_page_path']
                )
            )
        
        # Origin Access Identity for CloudFront
        oai = cloudfront.OriginAccessIdentity(
            self, "FrontendOAI",
            comment="OAI for Invoice Processor Frontend"
        )
        
        distribution = cloudfront.Distribution(
            self, "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    frontend_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object=self.config.CLOUDFRONT_DEFAULT_ROOT_OBJECT,
            error_responses=error_responses
        )
        
        # Grant CloudFront OAI access to S3 bucket
        frontend_bucket.grant_read(oai)

        # Deploy React build to S3
        s3deploy.BucketDeployment(
            self, "DeployFrontend",
            sources=[s3deploy.Source.asset("frontend/build")],
            destination_bucket=frontend_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
            cache_control=[
                s3deploy.CacheControl.no_cache()
            ]
        )

        # Outputs
        CfnOutput(
            self, "InvoiceLambdaArn",
            value=invoice_lambda.function_arn,
            description="Invoice processor Lambda function ARN"
        )

        CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description="API Gateway URL"
        )

        CfnOutput(
            self, "WebsiteUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="CloudFront URL"
        )

        CfnOutput(
            self, "S3BucketName",
            value=invoice_bucket.bucket_name,
            description="S3 bucket for invoices"
        )

        CfnOutput(
            self, "FrontendBucketName",
            value=frontend_bucket.bucket_name,
            description="S3 bucket for frontend"
        )
