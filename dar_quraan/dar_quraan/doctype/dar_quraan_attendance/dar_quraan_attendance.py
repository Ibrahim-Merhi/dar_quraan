import frappe
from frappe import _
from frappe.model.document import Document


class DarQuraanAttendance(Document):
	def validate(self):
		self.validate_session()
		self.fetch_session_context()
		self.validate_unique_attendance()
		self.populate_attendance_items_if_empty()
		self.validate_attendance_items()
		self.calculate_summary()
		self.validate_status()

	def validate_session(self):
		if not self.session:
			frappe.throw(_("Session is required."))

		if not frappe.db.exists(
			"Dar Quraan Session",
			self.session,
		):
			frappe.throw(_("Selected Session does not exist."))

	def get_session(self):
		return frappe.get_doc(
			"Dar Quraan Session",
			self.session,
		)

	def fetch_session_context(self):
		session = self.get_session()

		if session.status == "Cancelled":
			frappe.throw(_("Attendance cannot be recorded for " "a Cancelled Session."))

		self.attendance_date = session.session_date

		self.halaqa = session.halaqa

		self.halaqa_name = session.halaqa_name

		self.branch = session.branch

		self.teaching_location = session.teaching_location

		self.teacher = session.teacher

		self.academic_year = session.academic_year

		self.academic_term = session.academic_term

		if not self.attendance_date:
			frappe.throw(_("Selected Session does not have " "a Session Date."))

		if not self.halaqa:
			frappe.throw(_("Selected Session does not have " "a Halaqa."))

	def validate_unique_attendance(self):
		existing = frappe.db.exists(
			"Dar Quraan Attendance",
			{
				"session": self.session,
				"name": [
					"!=",
					self.name or "",
				],
			},
		)

		if existing:
			frappe.throw(_("Attendance already exists for " "Session {0}.").format(self.session))

	def populate_attendance_items_if_empty(self):
		"""
		Populate students only when the attendance table is empty.

		This is important because after the teacher changes statuses,
		subsequent saves must not overwrite the attendance rows.
		"""

		if self.get("attendance_items"):
			return

		assignments = self.get_active_student_assignments()

		for assignment in assignments:
			self.append(
				"attendance_items",
				{
					"student": (assignment.student),
					"student_name": (assignment.student_name),
					"student_assignment": (assignment.name),
					"attendance_status": ("Present"),
					"late_minutes": 0,
				},
			)

	def get_active_student_assignments(self):
		"""
		Return current Student Assignments for this Halaqa.

		If the Student Assignment DocType has a status field,
		only Active assignments are loaded.
		"""

		meta = frappe.get_meta("Dar Quraan Student Assignment")

		filters = {
			"halaqa": self.halaqa,
		}

		if meta.has_field("status"):
			filters["status"] = "Active"

		fields = [
			"name",
			"student",
		]

		if meta.has_field("student_name"):
			fields.append("student_name")

		assignments = frappe.get_all(
			"Dar Quraan Student Assignment",
			filters=filters,
			fields=fields,
			order_by="student asc",
		)

		for assignment in assignments:
			if not assignment.get("student_name"):
				assignment.student_name = (
					frappe.db.get_value(
						"Dar Quraan Student",
						assignment.student,
						"student_name",
					)
					or assignment.student
				)

		return assignments

	def validate_attendance_items(self):
		rows = self.get("attendance_items") or []

		if not rows:
			frappe.throw(_("No students are available for " "attendance in this Halaqa."))

		normalized_rows = []
		seen_assignments = set()

		for index, row in enumerate(
			rows,
			start=1,
		):
			row = self.get_attendance_item_document(
				row,
				index,
			)

			try:
				row.validate()

			except frappe.ValidationError as exc:
				frappe.throw(
					_("Attendance Item, row {0}: {1}").format(
						row.idx or index,
						str(exc),
					)
				)

			self.validate_item_assignment(row)

			if row.student_assignment in seen_assignments:
				frappe.throw(
					_("Student Assignment {0} appears " "more than once in Attendance.").format(
						row.student_assignment
					)
				)

			seen_assignments.add(row.student_assignment)

			normalized_rows.append(row)

		self.set(
			"attendance_items",
			normalized_rows,
		)

	def get_attendance_item_document(
		self,
		row,
		index,
	):
		if not isinstance(row, dict):
			return row

		row_data = dict(row)

		row_data.setdefault(
			"doctype",
			"Dar Quraan Attendance Item",
		)

		child = frappe.get_doc(row_data)

		child.idx = index

		return child

	def validate_item_assignment(
		self,
		row,
	):
		if not frappe.db.exists(
			"Dar Quraan Student Assignment",
			row.student_assignment,
		):
			frappe.throw(_("Student Assignment {0} does not exist.").format(row.student_assignment))

		assignment = frappe.db.get_value(
			"Dar Quraan Student Assignment",
			row.student_assignment,
			[
				"student",
				"halaqa",
			],
			as_dict=True,
		)

		if not assignment:
			frappe.throw(_("Student Assignment {0} does not exist.").format(row.student_assignment))

		if assignment.student != row.student:
			frappe.throw(
				_("Student in row {0} does not match " "the Student Assignment.").format(row.idx or 1)
			)

		if assignment.halaqa != self.halaqa:
			frappe.throw(
				_("Student Assignment in row {0} does not " "belong to this Halaqa.").format(row.idx or 1)
			)

	def calculate_summary(self):
		rows = self.get("attendance_items") or []

		self.total_students = len(rows)

		self.present_count = 0
		self.absent_count = 0
		self.late_count = 0
		self.excused_count = 0

		for row in rows:
			status = row.attendance_status

			if status == "Present":
				self.present_count += 1

			elif status == "Absent":
				self.absent_count += 1

			elif status == "Late":
				self.late_count += 1

			elif status == "Excused":
				self.excused_count += 1

	def validate_status(self):
		allowed_statuses = {
			"Draft",
			"Completed",
			"Cancelled",
		}

		if not self.status:
			self.status = "Draft"

		if self.status not in allowed_statuses:
			frappe.throw(_("Status must be Draft, Completed, " "or Cancelled."))
