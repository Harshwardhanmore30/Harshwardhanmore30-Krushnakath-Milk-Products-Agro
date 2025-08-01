from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from io import BytesIO
from models.database import Order, OrderItem
from flask import current_app

class InvoiceService:
    """Service class for generating PDF invoices"""
    
    @staticmethod
    def generate_invoice_pdf(order_id):
        """Generate PDF invoice for an order"""
        try:
            # Get order details
            order = Order.query.get(order_id)
            if not order:
                return None, "Order not found"

            if not order.items:
                return None, "Order has no items"
            
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#27ae60')
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#2c3e50')
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            # Add company logo
            logo_path = os.path.join(current_app.static_folder, 'images', 'logo.png')
            if os.path.exists(logo_path):
                try:
                    logo = Image(logo_path, width=2*inch, height=1*inch)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 12))
                except:
                    pass  # Skip logo if there's an issue
            
            # Company header
            company_style = ParagraphStyle(
                'Company',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2c3e50')
            )

            elements.append(Paragraph("<b>KrishnaKath Dairy</b>", title_style))
            elements.append(Paragraph("Premium Quality Dairy Products", company_style))
            elements.append(Paragraph("Address: Village Dairy Farm, Maharashtra, India", company_style))
            elements.append(Paragraph("Phone: +91-XXXXXXXXXX | Email: info@krishnakath.com", company_style))
            elements.append(Paragraph("GSTIN: 27XXXXX1234X1ZX (if applicable)", company_style))
            elements.append(Spacer(1, 20))
            
            # Invoice title
            elements.append(Paragraph("INVOICE", title_style))
            
            # Invoice details table
            invoice_data = [
                ['Invoice Number:', f'INV-{order.id:06d}'],
                ['Order ID:', f'#{order.id}'],
                ['Invoice Date:', datetime.now().strftime('%d %B %Y')],
                ['Order Date:', order.created_at.strftime('%d %B %Y')],
                ['Status:', order.status],
                ['Transaction ID:', order.transaction_id or 'N/A']
            ]
            
            invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
            invoice_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(invoice_table)
            elements.append(Spacer(1, 20))
            
            # Customer details
            elements.append(Paragraph("Bill To:", header_style))
            
            # Parse shipping address
            address_lines = order.shipping_address.split('\n')
            customer_info = ""
            for line in address_lines:
                customer_info += f"<para>{line}</para>"
            
            elements.append(Paragraph(customer_info, normal_style))
            elements.append(Spacer(1, 20))
            
            # Order items table
            elements.append(Paragraph("Order Details:", header_style))
            
            # Table headers
            item_data = [['S.No.', 'Product Name', 'Quantity', 'Unit Price (₹)', 'Total (₹)']]
            
            # Add order items
            for idx, item in enumerate(order.items, 1):
                item_data.append([
                    str(idx),
                    item.product.name,
                    str(item.quantity),
                    f"₹{item.price:.2f}",
                    f"₹{(item.quantity * item.price):.2f}"
                ])
            
            # Add total row
            item_data.append(['', '', '', 'Total Amount:', f"₹{order.total_amount:.2f}"])
            
            # Create table
            items_table = Table(item_data, colWidths=[0.8*inch, 3*inch, 1*inch, 1.5*inch, 1.5*inch])
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('GRID', (0, 0), (-1, -2), 1, colors.black),
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('ALIGN', (3, -1), (-1, -1), 'RIGHT'),
                ('GRID', (0, -1), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(items_table)
            elements.append(Spacer(1, 30))
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=6,
                alignment=TA_CENTER
            )

            elements.append(Paragraph("<b>Thank you for choosing KrishnaKath Dairy!</b>", footer_style))
            elements.append(Paragraph("For any queries, please contact us at info@krishnakath.com", footer_style))
            elements.append(Paragraph("This is a computer-generated invoice and does not require a signature.", footer_style))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data, None
            
        except Exception as e:
            return None, f"Error generating invoice: {str(e)}"
    
    @staticmethod
    def get_invoice_filename(order_id):
        """Generate invoice filename"""
        return f"Invoice_Order_{order_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
