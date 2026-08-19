# Dar Quraan User Guide

This guide explains how each role starts and uses Dar Quraan. Menu labels refer to the **Dar Quraan** workspace.

## 1. Common start for every user

1. Sign in with the account provided by the administrator.
2. Open **Dar Quraan** from the workspace sidebar.
3. Confirm that your expected shortcuts and lists are visible.
4. Use the global search bar to find a student, teacher, halaqa, application, or document number.
5. Never create a second record when the person or document already exists. Search first.
6. Do not change completed historical records merely to correct current placement. Create the appropriate transfer, follow-up, or new operational record.

Contact the Dar Quraan Manager if required records are hidden or an action is unavailable. Access is controlled by role and, for teachers, by assigned records.

## 2. Roles at a glance

| Role | Main responsibility | Typical access |
|---|---|---|
| Dar Quraan Manager | Configure and oversee the whole institute | Full operational, reporting, and setup access |
| Dar Quraan Supervisor | Review quality and supervise operations | Create/update operational and supervision records; limited destructive access |
| Dar Quraan Teacher | Teach and record assigned students' work | Assigned halaqas, students, attendance, progress, evaluations, exams, and follow-ups |
| Dar Quraan Data Entry | Maintain administrative data | Applications, students, assignments, and operational data without destructive access |
| Dar Quraan Viewer | Review information and reports | Read-only access |

System Manager remains responsible for technical Frappe configuration, users, email, SMS, backups, scheduler, and deployment.

## 3. Initial system setup — Manager

Complete setup in this order.

### 3.1 Settings and academic period

1. Open **Dar Quraan Settings**.
2. Configure absence, lateness, weak-result, no-progress, overdue-evaluation, and follow-up thresholds.
3. Configure notification recipients and enable email only after testing the outgoing email account.
4. Create **Dar Quraan Academic Year** and mark the current year.
5. Create its **Academic Term**.
6. Enable enrollment, attendance, and progress entry for the active period.

### 3.2 Organization

1. Create each **Branch**.
2. Create its **Teaching Locations**.
3. Create users and assign the correct Dar Quraan role.
4. Create each **Teacher** and link the teacher to their User account.
5. Create **Juz Levels**.
6. Create **Quran Programs** and their ordered milestones.
7. Create **Halaqas**, setting branch, location, academic period, teacher, capacity, and schedule.

### 3.3 Examination and discipline setup

1. Create **Error Rules** from the approved examination deduction sheet.
2. Confirm each rule's category, deduction, maximum occurrences, and active status.
3. Create **Discipline Rules** from the institute's approved internal policy.
4. Specify severity, default action, and whether guardian notification is mandatory.

Do not start admissions until branches, academic periods, teachers, programs, and halaqas are ready.

## 4. Online admission — Applicant and administration

### 4.1 Applicant

Open `/dar-quraan-admission` from the institute website.

1. Enter identity and contact information.
2. Enter education and employment information.
3. Select the admission goal and study track.
4. Describe current and previous Quran experience accurately.
5. Enter memorized juz, riwayah, previous sheikhs, ijazah, and Jazariyyah details when applicable.
6. Select preferred branch, days, and times.
7. Attach requested identity/supporting documents.
8. Submit the application and retain its reference number.

Submission creates a **Pending** Admission Application. It does not immediately create an active student.

### 4.2 Data Entry

1. Open **Admission Application** and filter by `Pending`.
2. Check identity, contact information, duplicates, documents, goal, level, and availability.
3. Correct administrative entry errors only when supported by the submitted documents.
4. Assign the application to the responsible reviewer.
5. Select **Start Review**.

### 4.3 Supervisor or Manager

1. Review the Quran background and arrange a placement evaluation when needed.
2. Select the proposed program, level, teacher, halaqa, and expected start date.
3. Select **Provisionally Approve** when a suitable place is available.
4. Select **Reject** only with a clear rejection reason.
5. When the applicant begins actual attendance, select **Finalize Admission**.

Final approval creates and links:

- an active **Student** profile;
- an active primary **Student Assignment**.

Do not manually create another student for an application already finalized.

## 5. Student placement and scheduling — Data Entry, Supervisor, Manager

1. Open the generated **Student Assignment**.
2. Verify branch, location, teacher, halaqa, academic period, program, track, riwayah, and level.
3. Create a **Student Weekly Slot**.
4. Select the weekday and start/end time.
5. Ensure the individual weekly duration is at least 30 minutes.
6. Use a transfer assignment when the student changes teacher, branch, or halaqa; preserve the previous assignment as history.

Only one appropriate current primary assignment should be active for the same period.

## 6. Daily teaching workflow — Teacher

Teachers see records within their assigned scope.

### 6.1 Before teaching

1. Open the assigned **Halaqa** and confirm its student assignments.
2. Review each student's latest Quran State and Next Assignment.
3. Open or create the day's **Session**.
4. Confirm date, time, location, teacher, academic year, and term.

### 6.2 Attendance

1. Open **Attendance** for the session.
2. Generate or verify the student rows.
3. Mark every student as Present, Absent, Late, or Excused.
4. Enter late minutes and excuse reason when applicable.
5. Add factual notes.
6. Complete the attendance record only after all rows are checked.

Never remove a student row merely to hide an absence.

### 6.3 Quran progress

1. Open **Student Progress** for the student's active assignment.
2. Record new memorization and revision ranges.
3. Add Progress Items with result, mistakes, prompts, memorization quality, Tajweed, and fluency.
4. Complete the record after review.
5. Review the updated **Student Quran State**.
6. Prepare or confirm the **Next Assignment**.

### 6.4 Evaluation

Use **Evaluation** for placement, monthly, periodic, final, or special academic evaluation.

1. Select the active Student Assignment.
2. Add Quran ranges/questions as Evaluation Items.
3. Record memorization, Tajweed, fluency, mistakes, prompts, and notes.
4. Complete the evaluation.
5. Create a Teacher Follow-up when intervention is required.

Routine Evaluation is not a substitute for the formal scientific-committee Exam record.

### 6.5 Jazariyyah and other texts

Use **Text Progress** to record:

- memorization percentage;
- explanation status;
- teacher assessment;
- completion notes.

A text can be completed only at 100% memorization, completed explanation, and a passing teacher assessment.

## 7. Follow-up and exceptions — Teacher, Supervisor, Manager

### 7.1 Teacher Follow-up

Create a follow-up for attendance, memorization, revision, Tajweed, fluency, evaluation, behavior, parent contact, or another academic concern.

1. Describe the issue objectively.
2. Record the required action and priority.
3. Set the next follow-up date when another review is required.
4. Add resolution notes before resolving it.

### 7.2 Exceptions

The daily scheduler detects configured issues such as repeated absence/lateness, weak results, missing progress, overdue evaluations/follow-ups, capacity, and missing assignments.

Supervisors should:

1. Review Open exceptions daily.
2. Acknowledge the exception when work begins.
3. Open the linked student/source record.
4. Take the appropriate operational action.
5. Record resolution notes and resolve it.

Resolving an exception does not alter its source record automatically.

## 8. Supervision — Supervisor

1. Create a **Supervision Visit** for a halaqa/session.
2. Choose scheduled, unannounced, remote, or follow-up visit.
3. Review session management, attendance, student progress, Quran performance, teacher adherence, and learning environment.
4. Add findings, ratings, corrective actions, owners, and due dates.
5. Create follow-up items where required.
6. Complete the visit with a clear summary.

Use evidence from attendance, progress, evaluations, and observation rather than general impressions.

## 9. Formal examinations — Teacher, Supervisor, Committee

Use **Exam**, not routine Evaluation, for formal milestones.

### 9.1 Eligibility

- **Five Juz:** verified completion must be a five-juz milestone.
- **Fifteen Juz Committee:** at least 15 completed juz.
- **Final 30 Juz:** exactly 30 completed juz.
- **Final 10 Juz:** 30 completed juz and prior 20 juz verified by the sheikh.

### 9.2 Committee

Committee exams require:

- at least three unique members;
- exactly one Chair;
- examiners/observer as applicable.

### 9.3 Questions and scoring

- Final 30 Juz: five memorization/performance questions and two Tajweed theory questions.
- Final 10 Juz: three memorization/performance questions and two Tajweed theory questions.
- Final allocation: 90 marks for memorization, performance, waqf and ibtida; 10 marks for Tajweed theory.
- Record each error against its configured Error Rule.
- The system calculates deductions and earned scores.
- Passing requires at least 80%.

Complete the exam only after questions, errors, scores, committee, and notes are verified.

## 10. Issuing an ijazah — Manager or Supervisor

An **Ijazah** requires a completed passing Final 30 Juz, Final 10 Juz, or Ijazah Retest with at least 80%.

1. Select the Student Assignment and passing Exam.
2. Confirm riwayah and qiraat method.
3. Select the granting sheikh and committee chair.
4. Enter the complete connected sanad text.
5. Set the grant date.
6. Attach the generated certificate when available.
7. Change status to Issued only after final verification.

Never issue an ijazah from a routine Evaluation. Revocation requires a recorded reason and should be restricted to authorized management.

## 11. Discipline — Teacher, Supervisor, Manager

1. Create a **Discipline Incident** against the active Student Assignment.
2. Select the approved Discipline Rule.
3. Record the event factually, without speculation or unnecessary personal data.
4. Apply or adjust the authorized action.
5. Notify the guardian when the rule requires it and record the notification date.
6. Obtain student acknowledgement when appropriate.
7. Add resolution notes before resolving the incident.

Serious suspension or dismissal decisions should be reviewed by management before changing the student's active status.

## 12. Reports — Manager, Supervisor, Viewer

Use the analytics reports for:

- student attendance, progress, and performance;
- teacher activity and attendance outcomes;
- halaqa capacity and performance;
- branch-level totals and comparisons.

Always set the reporting period and organizational filters before interpreting results. Investigate source documents when a number appears unexpected.

## 13. Viewer workflow

Viewers can inspect permitted records and analytics but must not edit operational information. A Viewer should:

1. Open the relevant report.
2. Apply branch, halaqa, teacher, student, and date filters.
3. Drill into source records when permitted.
4. Export information only when authorized by institute privacy policy.

## 14. System Manager operations

The System Manager should maintain:

- user accounts and roles;
- outgoing email and SMS Settings;
- scheduler and background workers;
- backups and restore tests;
- application updates and migrations;
- error logs and failed background jobs;
- website privacy, file-upload, and security settings.

After each deployment run:

```bash
bench --site SITE migrate
bench --site SITE clear-cache
bench --site SITE run-tests --app dar_quraan
```

## 15. Common problems

### A user cannot see expected students

Check that the user has the correct role, the Teacher record links to that User, and the active Student Assignment uses that Teacher.

### A student appears twice

Search by name, phone, email, national identity information, and application reference. Merge/correct under management control; do not continue using both records.

### Final admission fails

Confirm proposed program, teacher, halaqa, expected start date, and that the halaqa has branch and academic-year context.

### Attendance does not include a student

Confirm the Student Assignment is active/current and belongs to the session's halaqa and academic period.

### An exam cannot be completed

Check verified completed juz, exam format, committee size/chair, question counts, 90/10 allocation, and active Error Rules.

### Ijazah cannot be issued

Confirm the linked exam is a completed passing final exam with at least 80%, belongs to the same assignment, and includes the required sanad information.

### Notifications do not send

Confirm the relevant notification option is enabled and the System Manager has configured a working outgoing Email Account or SMS gateway. Test on staging before enabling production messages.

## 16. Data-quality rules

- Search before creating.
- Use the active Student Assignment as the context for operational records.
- Complete records only after review.
- Preserve historical assignments and completed records.
- Record reasons for rejection, cancellation, resolution, revocation, and disciplinary action.
- Store only necessary personal information and restrict exports.
- Keep identity documents private and follow the institute's retention policy.
