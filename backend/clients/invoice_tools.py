import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict

class InvoiceTools:
    def __init__(self, session_data: Dict[str, Any]):
        self.session_data = session_data
        self.invoices = session_data.get("invoices", [])
        self.embeddings = session_data.get("embeddings", np.array([]))
        self.texts = session_data.get("texts", [])
    
    def search_similar_invoices(self, query: str, limit: int = 5) -> List[Dict]:
        """Find invoices similar to the query using vector similarity."""
        if len(self.embeddings) == 0 or len(self.texts) == 0:
            return []
        
        try:
            # Create vectorizer for query
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            vectorizer.fit(self.texts)  # Fit on existing texts
            
            # Transform query
            query_vector = vectorizer.transform([query]).toarray()
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    invoice = self.invoices[idx]
                    results.append({
                        "invoice": invoice,
                        "similarity": float(similarities[idx]),
                        "snippet": self.texts[idx][:200] + "..."
                    })
            
            return results
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def aggregate_amounts(self, group_by: str = "vendor", operation: str = "sum") -> Dict[str, Any]:
        """Calculate aggregates (sum, avg, count, max, min) grouped by vendor, date, etc."""
        if not self.invoices:
            return {"error": "No invoices to aggregate"}
        
        groups = defaultdict(list)
        
        for invoice in self.invoices:
            data = invoice.get('data', {})
            amount = data.get('total_amount', 0)
            
            if not amount:
                continue
                
            # Group by different fields
            if group_by == "vendor":
                key = data.get('vendor_name', 'Unknown')
            elif group_by == "date":
                date_str = data.get('date', '')
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    key = date_obj.strftime('%Y-%m')  # Group by month
                except:
                    key = 'Unknown Date'
            elif group_by == "payment_terms":
                key = data.get('payment_terms', 'Unknown')
            else:
                key = "All"
            
            groups[key].append(float(amount))
        
        # Calculate aggregations
        results = {}
        total_sum = 0
        total_count = 0
        
        for group_name, amounts in groups.items():
            if operation == "sum":
                value = sum(amounts)
            elif operation == "avg":
                value = sum(amounts) / len(amounts)
            elif operation == "count":
                value = len(amounts)
            elif operation == "max":
                value = max(amounts)
            elif operation == "min":
                value = min(amounts)
            else:
                value = sum(amounts)
            
            results[group_name] = {
                "value": round(value, 2),
                "count": len(amounts),
                "amounts": amounts
            }
            
            total_sum += sum(amounts)
            total_count += len(amounts)
        
        return {
            "grouped_results": results,
            "summary": {
                "total_amount": round(total_sum, 2),
                "total_invoices": total_count,
                "average_amount": round(total_sum / max(total_count, 1), 2),
                "group_by": group_by,
                "operation": operation
            }
        }
    
    def filter_invoices(self, vendor: Optional[str] = None, 
                       amount_min: Optional[float] = None,
                       amount_max: Optional[float] = None,
                       date_start: Optional[str] = None,
                       date_end: Optional[str] = None,
                       payment_terms: Optional[str] = None) -> List[Dict]:
        """Filter invoices by various criteria."""
        filtered = []
        
        for invoice in self.invoices:
            data = invoice.get('data', {})
            
            # Vendor filter
            if vendor and vendor.lower() not in data.get('vendor_name', '').lower():
                continue
            
            # Amount filters
            amount = data.get('total_amount', 0)
            if amount_min and amount < amount_min:
                continue
            if amount_max and amount > amount_max:
                continue
            
            # Date filters
            invoice_date = data.get('date', '')
            if date_start or date_end:
                try:
                    inv_date = datetime.strptime(invoice_date, '%Y-%m-%d')
                    if date_start:
                        start_date = datetime.strptime(date_start, '%Y-%m-%d')
                        if inv_date < start_date:
                            continue
                    if date_end:
                        end_date = datetime.strptime(date_end, '%Y-%m-%d')
                        if inv_date > end_date:
                            continue
                except:
                    continue
            
            # Payment terms filter
            if payment_terms and payment_terms.lower() not in data.get('payment_terms', '').lower():
                continue
            
            filtered.append(invoice)
        
        return filtered
    
    def get_invoice_details(self, invoice_number: str) -> Optional[Dict]:
        """Get full details of a specific invoice by number."""
        for invoice in self.invoices:
            data = invoice.get('data', {})
            if data.get('invoice_number') == invoice_number:
                return invoice
        return None
    
    def get_vendor_summary(self) -> Dict[str, Any]:
        """Get summary statistics by vendor."""
        vendor_stats = defaultdict(lambda: {
            'invoices': [],
            'total_amount': 0,
            'count': 0,
            'avg_amount': 0
        })
        
        for invoice in self.invoices:
            data = invoice.get('data', {})
            vendor = data.get('vendor_name', 'Unknown')
            amount = data.get('total_amount', 0)
            
            vendor_stats[vendor]['invoices'].append(invoice)
            vendor_stats[vendor]['total_amount'] += amount
            vendor_stats[vendor]['count'] += 1
        
        # Calculate averages
        for vendor, stats in vendor_stats.items():
            if stats['count'] > 0:
                stats['avg_amount'] = round(stats['total_amount'] / stats['count'], 2)
        
        return dict(vendor_stats)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get overall summary of the current session's invoices."""
        if not self.invoices:
            return {"error": "No invoices in session"}
        
        total_amount = 0
        vendors = set()
        date_range = []
        payment_terms = defaultdict(int)
        
        for invoice in self.invoices:
            data = invoice.get('data', {})
            
            amount = data.get('total_amount', 0)
            total_amount += amount
            
            vendor = data.get('vendor_name')
            if vendor:
                vendors.add(vendor)
            
            date_str = data.get('date')
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    date_range.append(date_obj)
                except:
                    pass
            
            terms = data.get('payment_terms', 'Unknown')
            payment_terms[terms] += 1
        
        summary = {
            "total_invoices": len(self.invoices),
            "total_amount": round(total_amount, 2),
            "average_amount": round(total_amount / len(self.invoices), 2),
            "unique_vendors": len(vendors),
            "vendor_list": list(vendors),
            "payment_terms_breakdown": dict(payment_terms)
        }
        
        if date_range:
            summary["date_range"] = {
                "earliest": min(date_range).strftime('%Y-%m-%d'),
                "latest": max(date_range).strftime('%Y-%m-%d')
            }
        
        return summary

# Tool definitions for Claude
INVOICE_TOOLS = [
    {
        "name": "search_similar_invoices",
        "description": "Find invoices similar to a text query using semantic search",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query to find similar invoices"},
                "limit": {"type": "integer", "description": "Maximum number of results to return", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "aggregate_amounts",
        "description": "Calculate aggregated amounts grouped by vendor, date, or payment terms",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "enum": ["vendor", "date", "payment_terms"], "description": "Field to group by"},
                "operation": {"type": "string", "enum": ["sum", "avg", "count", "max", "min"], "description": "Aggregation operation"}
            },
            "required": ["group_by", "operation"]
        }
    },
    {
        "name": "filter_invoices",
        "description": "Filter invoices by various criteria like vendor, amount, date range",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor": {"type": "string", "description": "Filter by vendor name (partial match)"},
                "amount_min": {"type": "number", "description": "Minimum amount filter"},
                "amount_max": {"type": "number", "description": "Maximum amount filter"},
                "date_start": {"type": "string", "description": "Start date filter (YYYY-MM-DD)"},
                "date_end": {"type": "string", "description": "End date filter (YYYY-MM-DD)"},
                "payment_terms": {"type": "string", "description": "Filter by payment terms"}
            }
        }
    },
    {
        "name": "get_session_summary",
        "description": "Get overall summary statistics for all invoices in the current session",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_vendor_summary",
        "description": "Get detailed breakdown of spending by vendor",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
] 