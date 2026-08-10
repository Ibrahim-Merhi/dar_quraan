import frappe
from frappe import _


def get_or_create_quran_state(student_assignment):
    if not student_assignment:
        frappe.throw(
            _("Student Assignment is required.")
        )

    existing = frappe.db.exists(
        "Dar Quraan Student Quran State",
        {
            "student_assignment": student_assignment,
        },
    )

    if existing:
        return frappe.get_doc(
            "Dar Quraan Student Quran State",
            existing,
        )

    return frappe.get_doc(
        {
            "doctype": "Dar Quraan Student Quran State",
            "student_assignment": student_assignment,
            "status": "Active",
        }
    )


def update_state_from_progress(progress):
    if not progress:
        return

    if progress.status != "Completed":
        return

    if not progress.student_assignment:
        frappe.throw(
            _("Student Progress does not have a Student Assignment.")
        )

    state = get_or_create_quran_state(
        progress.student_assignment
    )

    state.last_progress = progress.name

    update_memorization_from_progress(
        state,
        progress,
    )

    update_revision_from_progress(
        state,
        progress,
    )

    state.save(
        ignore_permissions=True
    )

    return state


def update_memorization_from_progress(
    state,
    progress,
):
    items = progress.get(
        "progress_items"
    ) or []

    memorization_items = [
        item
        for item in items
        if item.progress_type == "New Memorization"
        and item.result in {
            "Excellent",
            "Very Good",
            "Good",
        }
    ]

    if not memorization_items:
        return

    last_item = memorization_items[-1]

    state.current_surah = (
        last_item.surah
    )

    state.current_ayah = (
        last_item.to_ayah
    )

    state.current_page = (
        last_item.to_page
    )


def update_revision_from_progress(
    state,
    progress,
):
    items = progress.get(
        "progress_items"
    ) or []

    revision_items = [
        item
        for item in items
        if item.progress_type == "Revision"
        and item.result in {
            "Excellent",
            "Very Good",
            "Good",
            "Needs Revision",
            "Repeat",
        }
    ]

    if not revision_items:
        return

    last_item = revision_items[-1]

    state.revision_surah = (
        last_item.surah
    )

    state.revision_from_ayah = (
        last_item.from_ayah
    )

    state.revision_to_ayah = (
        last_item.to_ayah
    )

    state.revision_from_page = (
        last_item.from_page
    )

    state.revision_to_page = (
        last_item.to_page
    )


def update_state_from_evaluation(
    evaluation,
):
    if not evaluation:
        return

    if evaluation.status != "Completed":
        return

    if not evaluation.student_assignment:
        frappe.throw(
            _("Evaluation does not have a Student Assignment.")
        )

    state = get_or_create_quran_state(
        evaluation.student_assignment
    )

    state.last_evaluation = (
        evaluation.name
    )

    state.save(
        ignore_permissions=True
    )

    return state


def update_state_from_next_assignment(
    next_assignment,
):
    if not next_assignment:
        return

    if next_assignment.status != "Assigned":
        return

    if not next_assignment.student_assignment:
        frappe.throw(
            _(
                "Next Assignment does not have "
                "a Student Assignment."
            )
        )

    state = get_or_create_quran_state(
        next_assignment.student_assignment
    )

    state.last_next_assignment = (
        next_assignment.name
    )

    state.save(
        ignore_permissions=True
    )

    return state