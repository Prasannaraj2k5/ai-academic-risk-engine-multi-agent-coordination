"""Deterministic Synthetic Dataset Generator for AI Academic Early-Warning Engine.

Generates:
- 60 CSE-A students (STU101 - STU160)
- 300 academic subject records (5 courses per student)
- 1200 assignment records (20 assignments per student)
- Historical intervention records & catalog
- Guaranteed exact metrics for STU104 demo case
- Cohort risk distribution: 2 Critical, 3 High, 10 Medium, 45 Low (Total: 60)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent

COURSES = [
    ("CS301", "Data Structures & Algorithms"),
    ("CS302", "Design & Analysis of Algorithms"),
    ("CS303", "Database Management Systems"),
    ("CS304", "Operating Systems Principles"),
    ("CS305", "Computer Networks & Protocols"),
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Advait", "Ananya", "Arjun", "Dev", "Diya", "Ishaan",
    "Kavya", "Manish", "Meera", "Neha", "Nikhil", "Pooja", "Pranav", "Priya",
    "Rahul", "Riya", "Rohan", "Sanjay", "Shreya", "Siddharth", "Sneha", "Tanvi",
    "Tarun", "Varun", "Vikram", "Zoya", "Kunal", "Simran", "Akash", "Bhavna",
    "Chetan", "Deepika", "Gaurav", "Harsh", "Indira", "Jaspreet", "Karan", "Lavanya",
    "Mohit", "Naveen", "Ojas", "Payal", "Radhika", "Sameer", "Tanya", "Umesh",
    "Vandana", "Yash", "Abhinav", "Divya", "Esha", "Farhan", "Geeta", "Hemant",
    "Ishita", "Jay", "Kritika", "Lakshay"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Iyer", "Reddy", "Gupta", "Nair", "Mehta",
    "Kulkarni", "Deshmukh", "Chopra", "Malhotra", "Bhat", "Rao", "Joshi",
    "Saxena", "Mishra", "Pandey", "Kapoor", "Singhania", "Aggarwal", "Bansal",
    "Choudhury", "Das", "Ghosh", "Mukherjee", "Chatterjee", "Banerjee", "Sen", "Roy",
    "Kumar", "Singh", "Prasad", "Varma", "Soni", "Bhardwaj", "Pandit", "Acharya",
    "Pillai", "Menon", "Shetty", "Hegde", "Naik", "Gowda", "Patil", "Shinde",
    "Jadhav", "More", "Pawar", "Bhosale", "Kadam", "Sawant", "Thakur", "Rathore",
    "Chauhan", "Solanki", "Parmar", "Dutta", "Saha", "Bhattacharya"
]


def generate_all_datasets():
    np.random.seed(42)

    # 1. Generate 60 students
    students = []
    # Target distribution across 60 students:
    # Critical: 2 (STU104, STU112)
    # High: 3 (STU118, STU125, STU139)
    # Medium: 10 (STU107, STU115, STU121, STU128, STU133, STU141, STU146, STU150, STU154, STU158)
    # Low: 45 (Remaining)

    critical_ids = {"STU104", "STU112"}
    high_ids = {"STU118", "STU125", "STU139"}
    medium_ids = {
        "STU107", "STU115", "STU121", "STU128", "STU133",
        "STU141", "STU146", "STU150", "STU154", "STU158"
    }

    for idx in range(101, 161):
        sid = f"STU{idx}"
        fn_idx = (idx - 101) % len(FIRST_NAMES)
        ln_idx = (idx - 101) % len(LAST_NAMES)
        # Ensure STU104 has recognizable name
        if sid == "STU104":
            full_name = "Rohan Verma"
            prior_avg = 74.0
        elif sid in critical_ids:
            full_name = f"{FIRST_NAMES[fn_idx]} {LAST_NAMES[ln_idx]}"
            prior_avg = 72.5
        elif sid in high_ids:
            full_name = f"{FIRST_NAMES[fn_idx]} {LAST_NAMES[ln_idx]}"
            prior_avg = 75.0
        elif sid in medium_ids:
            full_name = f"{FIRST_NAMES[fn_idx]} {LAST_NAMES[ln_idx]}"
            prior_avg = 78.0
        else:
            full_name = f"{FIRST_NAMES[fn_idx]} {LAST_NAMES[ln_idx]}"
            prior_avg = round(float(np.random.uniform(76.0, 88.0)), 1)

        students.append({
            "student_id": sid,
            "name": full_name,
            "section": "CSE-A",
            "semester": 5,
            "department": "Computer Science & Engineering",
            "prior_semester_avg": prior_avg,
            "advisor_name": "Dr. K. Raman",
            "email": f"{sid.lower()}@academics.edu",
        })

    df_students = pd.DataFrame(students)
    df_students.to_csv(DATA_DIR / "students.csv", index=False)
    print(f"Saved {len(df_students)} students to students.csv")

    # 2. Academic Records (300 records = 60 * 5)
    records = []
    for s in students:
        sid = s["student_id"]
        if sid == "STU104":
            # EXACT REQUIRED VALUES FOR STU104:
            # Overall Attendance: 68.0%
            # Current Average: 54.7%
            # Failed Assessments: 2 (CS301, CS302)
            # Courses marks: 48.0, 45.0, 58.0, 60.0, 62.5 -> Avg = 273.5 / 5 = 54.7
            # Attendance: 65, 62, 72, 70, 71 -> Avg = 340 / 5 = 68.0
            stu104_marks = [48.0, 45.0, 58.0, 60.0, 62.5]
            stu104_att = [65.0, 62.0, 72.0, 70.0, 71.0]

            for c_idx, (ccode, cname) in enumerate(COURSES):
                m = stu104_marks[c_idx]
                att = stu104_att[c_idx]
                records.append({
                    "student_id": sid,
                    "course_code": ccode,
                    "course_name": cname,
                    "attendance_pct": att,
                    "internal_marks": round(m * 0.3, 1),
                    "midterm_marks": round(m * 0.3, 1),
                    "final_assessment_marks": round(m * 0.4, 1),
                    "total_marks": m,
                    "passed": m >= 50.0,
                })
        elif sid in critical_ids:  # STU112
            # Critical: Attendance ~64%, Avg ~52%, Failed: 2
            marks_list = [46.0, 48.0, 55.0, 56.0, 55.0]
            att_list = [62.0, 63.0, 65.0, 64.0, 66.0]
            for c_idx, (ccode, cname) in enumerate(COURSES):
                m = marks_list[c_idx]
                att = att_list[c_idx]
                records.append({
                    "student_id": sid,
                    "course_code": ccode,
                    "course_name": cname,
                    "attendance_pct": att,
                    "internal_marks": round(m * 0.3, 1),
                    "midterm_marks": round(m * 0.3, 1),
                    "final_assessment_marks": round(m * 0.4, 1),
                    "total_marks": m,
                    "passed": m >= 50.0,
                })
        elif sid in high_ids:
            # High Risk: Attendance ~72%, Avg ~60-64%, Failed: 1 (Yields High Risk 50-74)
            marks_base = [48.0, 60.0, 62.0, 64.0, 66.0]
            att_base = [71.0, 72.0, 73.0, 72.0, 72.0]
            for c_idx, (ccode, cname) in enumerate(COURSES):
                m = marks_base[c_idx]
                att = att_base[c_idx]
                records.append({
                    "student_id": sid,
                    "course_code": ccode,
                    "course_name": cname,
                    "attendance_pct": att,
                    "internal_marks": round(m * 0.3, 1),
                    "midterm_marks": round(m * 0.3, 1),
                    "final_assessment_marks": round(m * 0.4, 1),
                    "total_marks": m,
                    "passed": m >= 50.0,
                })
        elif sid in medium_ids:
            # Medium Risk: Attendance ~72-76%, Avg ~64-68%, Failed: 0
            marks_base = [62.0, 65.0, 66.0, 68.0, 70.0]
            att_base = [73.0, 74.0, 75.0, 76.0, 74.0]
            for c_idx, (ccode, cname) in enumerate(COURSES):
                m = marks_base[c_idx]
                att = att_base[c_idx]
                records.append({
                    "student_id": sid,
                    "course_code": ccode,
                    "course_name": cname,
                    "attendance_pct": att,
                    "internal_marks": round(m * 0.3, 1),
                    "midterm_marks": round(m * 0.3, 1),
                    "final_assessment_marks": round(m * 0.4, 1),
                    "total_marks": m,
                    "passed": True,
                })
        else:
            # Low Risk: Attendance >= 80%, Avg >= 75%, Failed: 0
            base_att = float(np.random.uniform(80.0, 95.0))
            base_m = float(np.random.uniform(74.0, 92.0))
            for c_idx, (ccode, cname) in enumerate(COURSES):
                m = round(float(np.clip(base_m + np.random.uniform(-4.0, 4.0), 65.0, 98.0)), 1)
                att = round(float(np.clip(base_att + np.random.uniform(-3.0, 3.0), 75.0, 98.0)), 1)
                records.append({
                    "student_id": sid,
                    "course_code": ccode,
                    "course_name": cname,
                    "attendance_pct": att,
                    "internal_marks": round(m * 0.3, 1),
                    "midterm_marks": round(m * 0.3, 1),
                    "final_assessment_marks": round(m * 0.4, 1),
                    "total_marks": m,
                    "passed": True,
                })

    df_records = pd.DataFrame(records)
    df_records.to_csv(DATA_DIR / "academic_records.csv", index=False)
    print(f"Saved {len(df_records)} records to academic_records.csv")

    # 3. Assignment Records (1200 records = 60 * 20)
    assignments = []
    for s in students:
        sid = s["student_id"]
        # STU104 exact requirements:
        # Total Assignments: 20
        # Missed: 2
        # Late: 4
        # Submitted: 14
        if sid == "STU104":
            # 20 assignments, exactly 2 missed, 4 late, 14 submitted
            statuses = ["missed"] * 2 + ["late"] * 4 + ["submitted"] * 14
            for a_idx in range(1, 21):
                ccode, _ = COURSES[(a_idx - 1) % len(COURSES)]
                st = statuses[a_idx - 1]
                score = 0 if st == "missed" else (65 if st == "late" else 85)
                assignments.append({
                    "assignment_id": f"ASN_{sid}_{a_idx:02d}",
                    "student_id": sid,
                    "course_code": ccode,
                    "assignment_num": a_idx,
                    "status": st,
                    "score": score,
                    "submission_delay_days": 5 if st == "late" else (0 if st == "submitted" else -1),
                    "due_week": ((a_idx - 1) // 5) + 1,
                })
        elif sid in critical_ids:
            # Critical: 3 missed, 3 late, 14 submitted
            statuses = ["missed"] * 3 + ["late"] * 3 + ["submitted"] * 14
            for a_idx in range(1, 21):
                ccode, _ = COURSES[(a_idx - 1) % len(COURSES)]
                st = statuses[a_idx - 1]
                score = 0 if st == "missed" else (60 if st == "late" else 80)
                assignments.append({
                    "assignment_id": f"ASN_{sid}_{a_idx:02d}",
                    "student_id": sid,
                    "course_code": ccode,
                    "assignment_num": a_idx,
                    "status": st,
                    "score": score,
                    "submission_delay_days": 4 if st == "late" else (0 if st == "submitted" else -1),
                    "due_week": ((a_idx - 1) // 5) + 1,
                })
        elif sid in high_ids:
            # High: 1 missed, 4 late, 15 submitted
            statuses = ["missed"] * 1 + ["late"] * 4 + ["submitted"] * 15
            for a_idx in range(1, 21):
                ccode, _ = COURSES[(a_idx - 1) % len(COURSES)]
                st = statuses[a_idx - 1]
                score = 0 if st == "missed" else (70 if st == "late" else 82)
                assignments.append({
                    "assignment_id": f"ASN_{sid}_{a_idx:02d}",
                    "student_id": sid,
                    "course_code": ccode,
                    "assignment_num": a_idx,
                    "status": st,
                    "score": score,
                    "submission_delay_days": 3 if st == "late" else (0 if st == "submitted" else -1),
                    "due_week": ((a_idx - 1) // 5) + 1,
                })
        elif sid in medium_ids:
            # Medium: 0 missed, 3 late, 17 submitted
            statuses = ["missed"] * 0 + ["late"] * 3 + ["submitted"] * 17
            for a_idx in range(1, 21):
                ccode, _ = COURSES[(a_idx - 1) % len(COURSES)]
                st = statuses[a_idx - 1]
                score = 75 if st == "late" else 85
                assignments.append({
                    "assignment_id": f"ASN_{sid}_{a_idx:02d}",
                    "student_id": sid,
                    "course_code": ccode,
                    "assignment_num": a_idx,
                    "status": st,
                    "score": score,
                    "submission_delay_days": 2 if st == "late" else 0,
                    "due_week": ((a_idx - 1) // 5) + 1,
                })
        else:
            # Low: 0 missed, 0-1 late, remaining submitted
            late_count = 1 if np.random.rand() > 0.7 else 0
            statuses = ["late"] * late_count + ["submitted"] * (20 - late_count)
            np.random.shuffle(statuses)
            for a_idx in range(1, 21):
                ccode, _ = COURSES[(a_idx - 1) % len(COURSES)]
                st = statuses[a_idx - 1]
                score = int(np.random.randint(75, 88)) if st == "late" else int(np.random.randint(85, 100))
                assignments.append({
                    "assignment_id": f"ASN_{sid}_{a_idx:02d}",
                    "student_id": sid,
                    "course_code": ccode,
                    "assignment_num": a_idx,
                    "status": st,
                    "score": score,
                    "submission_delay_days": 2 if st == "late" else 0,
                    "due_week": ((a_idx - 1) // 5) + 1,
                })

    df_assignments = pd.DataFrame(assignments)
    df_assignments.to_csv(DATA_DIR / "assignments.csv", index=False)
    print(f"Saved {len(df_assignments)} assignments to assignments.csv")

    # 4. Interventions Knowledge Catalog (interventions.json)
    interventions_catalog = {
        "interventions": [
            {
                "id": "INT_ATT_01",
                "trigger": "Low attendance",
                "title": "Structured Attendance Improvement Plan",
                "description": "Establish a mandatory daily attendance verification protocol with faculty advisor check-ins every Monday.",
                "target_factor": "Attendance",
                "urgency": "High",
                "duration_weeks": 4,
                "oversight_required": True
            },
            {
                "id": "INT_ATT_02",
                "trigger": "Critical attendance",
                "title": "Mandatory Faculty Counseling",
                "description": "One-on-one counseling with Department Chair and Academic Counselor to evaluate attendance barriers and formulate remediation.",
                "target_factor": "Attendance",
                "urgency": "Immediate",
                "duration_weeks": 2,
                "oversight_required": True
            },
            {
                "id": "INT_PERF_01",
                "trigger": "Performance decline",
                "title": "Academic Mentoring Program",
                "description": "Pair student with a senior faculty mentor to conduct bi-weekly study progress diagnostics and concept clarification.",
                "target_factor": "Performance",
                "urgency": "Medium",
                "duration_weeks": 6,
                "oversight_required": True
            },
            {
                "id": "INT_PERF_02",
                "trigger": "Failed assessments",
                "title": "Remedial Subject Tutorials",
                "description": "Enroll student into specialized remedial tutorial cohorts for subjects scoring below passing threshold (<50%).",
                "target_factor": "Assessments",
                "urgency": "Immediate",
                "duration_weeks": 6,
                "oversight_required": True
            },
            {
                "id": "INT_ASN_01",
                "trigger": "Missed assignments",
                "title": "Assignment Recovery Plan",
                "description": "Provide a structured 14-day schedule for submission of missed coursework and late deliverables with guided office hours.",
                "target_factor": "Assignments",
                "urgency": "High",
                "duration_weeks": 3,
                "oversight_required": False
            },
            {
                "id": "INT_HIST_01",
                "trigger": "Prior academic warning",
                "title": "Academic Probation Monitoring Agreement",
                "description": "Comprehensive academic contract with bi-weekly milestone milestones signed by student, advisor, and department head.",
                "target_factor": "History",
                "urgency": "High",
                "duration_weeks": 8,
                "oversight_required": True
            }
        ]
    }
    with open(DATA_DIR / "interventions.json", "w", encoding="utf-8") as f:
        json.dump(interventions_catalog, f, indent=2)
    print("Saved interventions catalog to interventions.json")

    # 5. Sample History (sample_history.json)
    history_records = [
        {
            "student_id": "STU104",
            "semester": 4,
            "recorded_risk_score": 58,
            "risk_band": "HIGH",
            "historical_flags": ["Prior semester attendance warning", "Midterm slump in CS202"],
            "history_contribution_score": 7,
            "interventions_taken": ["Informal faculty discussion on attendance"],
            "outcome": "Partial recovery to 74% final semester average"
        },
        {
            "student_id": "STU112",
            "semester": 4,
            "recorded_risk_score": 62,
            "risk_band": "HIGH",
            "historical_flags": ["Prior assessment backlog"],
            "history_contribution_score": 8,
            "interventions_taken": ["Tutorial support"],
            "outcome": "Borderline pass"
        },
        {
            "student_id": "STU118",
            "semester": 4,
            "recorded_risk_score": 42,
            "risk_band": "MEDIUM",
            "historical_flags": ["Occasional late submissions"],
            "history_contribution_score": 4,
            "interventions_taken": [],
            "outcome": "Standard progress"
        }
    ]
    with open(DATA_DIR / "sample_history.json", "w", encoding="utf-8") as f:
        json.dump(history_records, f, indent=2)
    print("Saved sample history to sample_history.json")


if __name__ == "__main__":
    generate_all_datasets()
