from collections import defaultdict
from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class DarQuraanExam(Document):
	FORMATS: ClassVar[dict[str, tuple[int, int, bool]]] = {
		"Fifteen Juz Committee": (3, 1, True),
		"Final 30 Juz": (5, 2, True),
		"Final 10 Juz": (3, 2, True),
	}

	def validate(self):
		self.set_assignment_context()
		self.validate_milestone_eligibility()
		self.validate_committee()
		self.validate_question_format()
		self.calculate_scores()

	def set_assignment_context(self):
		assignment = frappe.db.get_value(
			"Dar Quraan Student Assignment",
			self.student_assignment,
			["student", "student_name", "teacher", "riwayah"],
			as_dict=True,
		)
		if not assignment:
			frappe.throw(_("Student Assignment does not exist."))
		self.student, self.student_name = assignment.student, assignment.student_name
		self.riwayah = self.riwayah or assignment.riwayah
		self.examiner_teacher = self.examiner_teacher or assignment.teacher

	def validate_milestone_eligibility(self):
		completed = cint(self.completed_juz_at_exam)
		if not 0 <= completed <= 30:
			frappe.throw(_("Verified Completed Juz must be between 0 and 30."))
		if self.exam_type == "Five Juz" and (completed < 5 or completed % 5):
			frappe.throw(_("Five Juz exams are allowed only at completed five-juz milestones."))
		if self.exam_type == "Fifteen Juz Committee" and completed < 15:
			frappe.throw(_("The scientific committee exam requires at least 15 completed Juz."))
		if self.exam_type == "Final 30 Juz" and completed != 30:
			frappe.throw(_("The Final 30 Juz exam requires all 30 Juz."))
		if self.exam_type == "Final 10 Juz" and (completed != 30 or not cint(self.prior_twenty_juz_verified)):
			frappe.throw(
				_(
					"The Final 10 Juz exam requires 30 completed Juz and verification of the other 20 Juz by the Sheikh."
				)
			)

	def validate_committee(self):
		members = [row.member for row in self.committee]
		if len(members) != len(set(members)):
			frappe.throw(_("Committee members must be unique."))
		if self.exam_type in self.FORMATS and self.FORMATS[self.exam_type][2]:
			if len(members) < 3:
				frappe.throw(_("This exam requires at least three scientific committee members."))
			if sum(row.role == "Chair" for row in self.committee) != 1:
				frappe.throw(_("The scientific committee requires exactly one Chair."))

	def validate_question_format(self):
		memorization = [row for row in self.questions if row.category == "Memorization and Performance"]
		tajweed = [row for row in self.questions if row.category == "Tajweed Theory"]
		if self.exam_type in self.FORMATS:
			required_mem, required_tajweed, committee_required = self.FORMATS[self.exam_type]
			del committee_required
			if len(memorization) != required_mem or len(tajweed) != required_tajweed:
				frappe.throw(
					_("{0} requires {1} memorization questions and {2} Tajweed questions.").format(
						self.exam_type, required_mem, required_tajweed
					)
				)
		if self.exam_type in {"Final 30 Juz", "Final 10 Juz", "Ijazah Retest"}:
			if (
				flt(sum(row.max_score for row in memorization), 2) != 90
				or flt(sum(row.max_score for row in tajweed), 2) != 10
			):
				frappe.throw(
					_(
						"Final Ijazah exams must allocate 90 marks to memorization/performance and 10 marks to Tajweed theory."
					)
				)

	def calculate_scores(self):
		deductions = defaultdict(float)
		for error in self.errors:
			rule = frappe.db.get_value(
				"Dar Quraan Error Rule",
				error.error_rule,
				["deduction", "maximum_occurrences", "active"],
				as_dict=True,
			)
			if not rule or not rule.active:
				frappe.throw(_("Error Rule {0} is missing or inactive.").format(error.error_rule))
			count = cint(error.error_count)
			if count <= 0:
				frappe.throw(_("Error Count must be greater than zero."))
			if cint(rule.maximum_occurrences) and count > cint(rule.maximum_occurrences):
				frappe.throw(_("Error count exceeds the rule maximum."))
			error.deduction_each = flt(rule.deduction)
			error.total_deduction = flt(count * error.deduction_each, 2)
			deductions[error.question] += error.total_deduction
		mem_score = tajweed_score = 0.0
		for row in self.questions:
			row.deduction = flt(deductions[row.name], 2)
			row.earned_score = max(0, flt(row.max_score) - row.deduction)
			if row.category == "Tajweed Theory":
				tajweed_score += row.earned_score
			else:
				mem_score += row.earned_score
		self.memorization_score = flt(mem_score, 2)
		self.tajweed_score = flt(tajweed_score, 2)
		self.final_score = flt(mem_score + tajweed_score, 2)
		self.result = (
			"Pending"
			if self.status == "Draft"
			else ("Passed" if self.final_score >= flt(self.passing_score) else "Failed")
		)
