import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class DarQuraanSurah(Document):
	def validate(self):
		self.validate_surah_number()
		self.validate_ayah_count()
		self.validate_page_range()
		self.validate_juz_range()

	def validate_surah_number(self):
		surah_number = cint(self.surah_number)

		if surah_number < 1 or surah_number > 114:
			frappe.throw(_("Surah Number must be between 1 and 114."))

	def validate_ayah_count(self):
		ayah_count = cint(self.ayah_count)

		if ayah_count < 1:
			frappe.throw(_("Ayah Count must be greater than zero."))

	def validate_page_range(self):
		start_page = cint(self.start_page)
		end_page = cint(self.end_page)

		if start_page < 1 or start_page > 604:
			frappe.throw(_("Start Page must be between 1 and 604."))

		if end_page < 1 or end_page > 604:
			frappe.throw(_("End Page must be between 1 and 604."))

		if end_page < start_page:
			frappe.throw(_("End Page cannot be before Start Page."))

	def validate_juz_range(self):
		start_juz = cint(self.start_juz)
		end_juz = cint(self.end_juz)

		if start_juz < 1 or start_juz > 30:
			frappe.throw(_("Start Juz must be between 1 and 30."))

		if end_juz < 1 or end_juz > 30:
			frappe.throw(_("End Juz must be between 1 and 30."))

		if end_juz < start_juz:
			frappe.throw(_("End Juz cannot be before Start Juz."))
