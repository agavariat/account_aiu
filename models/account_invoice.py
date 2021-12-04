from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)
class AccountInvoice(models.Model):
	_inherit = 'account.invoice'

	@api.one
	@api.depends('invoice_line_ids.price_subtotal_aiu', 'type', 'currency_id')
	def _compute_amount_total_aiu(self):
		round_curr = self.currency_id.round
		self.amount_total_price_aiu = sum(round_curr(line.price_subtotal_aiu) for line in self.invoice_line_ids)
		line_numbers = len(self.invoice_line_ids)
		if self.amount_total_price_aiu > 0.0 and line_numbers > 1:
			for line in self.invoice_line_ids:
				price = (self.amount_total_price_aiu * 0.1)
				line_numbers -= 1
				if line_numbers != 0:
					price = self.amount_total_price_aiu - price
				line.price_unit = price
				# line.update({'price_unit': price})
				line._compute_price()

	amount_total_price_aiu = fields.Monetary(string='Total amount aiu', store=True, readonly=True, compute="_compute_amount_total_aiu")

class AccountInvoiceLine(models.Model):
	_inherit = 'account.invoice.line'

	@api.one
	@api.depends('price_aiu', 'quantity', 'invoice_line_tax_ids',
		'product_id', 'invoice_id.type', 
		'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
	def _compute_price_aiu(self):
		currency = self.invoice_id and self.invoice_id.currency_id or None
		price = 0.0
		if self.invoice_id.type[:3] == 'out':
			price = self.price_aiu * (1 - (self.discount or 0.0) / 100.0)

		taxes = False
		if self.invoice_line_tax_ids:
			taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)

		self.price_subtotal_aiu = taxes['total_excluded'] if taxes else self.quantity * price
		self.price_total_aiu = taxes['total_included'] if taxes else self.price_subtotal

		# total = 0.0
		# if self.invoice_id.type[:3] == 'out':
		# 	total = self.price_aiu * self.quantity
		# sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
		# self.price_subtotal_aiu = total * sign

	price_aiu = fields.Float(string="Precio unit", required=True, digits=dp.get_precision('Product Price'))
	price_subtotal_aiu = fields.Monetary(string='Amount aiu (without Taxes)',
		store=True, readonly=True, compute='_compute_price_aiu', help="Total amount without taxes")
	price_total_aiu = fields.Monetary(string='Total Amount aiu (without Taxes)',
		store=True, readonly=True, compute='_compute_price_aiu', help="Total amount without taxes")
