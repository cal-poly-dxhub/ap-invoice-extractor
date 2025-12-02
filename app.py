#!/usr/bin/env python3
from aws_cdk import App
from infrastructure.invoice_processor_stack import InvoiceProcessorStack
from config import get_config

config = get_config()
app = App()

InvoiceProcessorStack(app, config.get_stack_name())

app.synth()