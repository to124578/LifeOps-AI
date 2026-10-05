# demo documents (all fictional) and the canned outputs for mock mode.
# {date:+7} -> "11 October 2026", {iso:+7} -> "2026-10-11" so dates never go stale
import re
from datetime import date, timedelta

_TOKEN = re.compile(r"\{(date|iso):([+-]?\d+)\}")


def render(obj, today: date):
    if isinstance(obj, str):
        def sub(m):
            d = today + timedelta(days=int(m.group(2)))
            return f"{d.day} {d:%B %Y}" if m.group(1) == "date" else d.isoformat()
        return _TOKEN.sub(sub, obj)
    if isinstance(obj, list):
        return [render(x, today) for x in obj]
    if isinstance(obj, dict):
        return {k: render(v, today) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------- A: internship offer
OFFER_TEXT = """Subject: Offer of Internship - Software Engineering Intern (Ref: OFFER-7781)
From: Priya Nair, HR Coordinator, Brightwave Technologies <hr@brightwave-demo.example>
Date: {date:+0}

Dear Candidate,

Congratulations! We are pleased to offer you the position of Software Engineering Intern at Brightwave Technologies for a duration of 8 weeks, with a monthly stipend of Rs. 25,000.

To accept this offer, please sign the attached offer letter and return a scanned copy to hr@brightwave-demo.example within 24 hours of receiving this email.

Along with the signed letter, please attach:
1. A scanned copy of a government-issued photo ID
2. Your latest college marksheet
3. A no-objection letter from your college (NOC)

Your joining date is {date:+14}. Please report to the Pune office by 9:30 AM on that day and carry the originals of all the documents listed above.

Please note that the NOC must be issued on your college letterhead and signed by the Training & Placement Officer.

Regards,
Priya Nair
HR Coordinator, Brightwave Technologies
"""

OFFER_U = {
    "title": "Internship offer - Brightwave Technologies",
    "document_type": "job offer email",
    "language": "en",
    "summary": "Offer for an 8-week Software Engineering Internship. Accepting requires signing and returning the offer letter with ID, marksheet and NOC within 24 hours of receipt; joining is on {date:+14}.",
    "sensitive_domains": ["employment"],
    "actions": [
        {"id": "a1", "title": "Get the No-Objection Letter (NOC) from your college", "description": "Must be on college letterhead and signed by the Training & Placement Officer.", "owner": "You (with your college T&P Officer)", "priority": "high", "effort_minutes": 120, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "the NOC must be issued on your college letterhead and signed by the Training & Placement Officer"},
        {"id": "a2", "title": "Scan your government photo ID and latest marksheet", "description": "Both are to be attached to the return email.", "owner": "You", "priority": "high", "effort_minutes": 20, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "A scanned copy of a government-issued photo ID"},
        {"id": "a3", "title": "Sign the offer letter", "description": "Sign the attached offer letter.", "owner": "You", "priority": "high", "effort_minutes": 10, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "please sign the attached offer letter"},
        {"id": "a4", "title": "Email the signed letter and all attachments to HR", "description": "Send a scanned copy of the signed letter with ID, marksheet and NOC to hr@brightwave-demo.example.", "owner": "You", "priority": "high", "effort_minutes": 10, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "return a scanned copy to hr@brightwave-demo.example within 24 hours of receiving this email"},
        {"id": "a5", "title": "Report to the Pune office with original documents", "description": "Arrive by 9:30 AM on the joining date carrying originals of all listed documents.", "owner": "You", "priority": "medium", "effort_minutes": None, "due_at": "{iso:+14}T09:30", "can_delegate": None, "confidence": "high", "evidence": "Please report to the Pune office by 9:30 AM on that day and carry the originals of all the documents listed above."},
    ],
    "deadlines": [
        {"id": "d1", "label": "Sign and return the offer letter", "due_at": None, "date_text": "within 24 hours of receiving this email", "relative_hours": 24, "kind": "hard", "action_ids": ["a4"], "confidence": "medium", "evidence": "return a scanned copy to hr@brightwave-demo.example within 24 hours of receiving this email"},
        {"id": "d2", "label": "Joining date - report to Pune office", "due_at": "{iso:+14}T09:30", "date_text": "{date:+14}, 9:30 AM", "relative_hours": None, "kind": "event", "action_ids": ["a5"], "confidence": "high", "evidence": "Your joining date is {date:+14}."},
    ],
    "requirements": [
        {"item": "Signed offer letter", "required": True, "action_ids": ["a3", "a4"], "confidence": "high", "evidence": "sign the attached offer letter"},
        {"item": "Scanned government-issued photo ID", "required": True, "action_ids": ["a2", "a4"], "confidence": "high", "evidence": "A scanned copy of a government-issued photo ID"},
        {"item": "Latest college marksheet", "required": True, "action_ids": ["a2", "a4"], "confidence": "high", "evidence": "Your latest college marksheet"},
        {"item": "No-objection letter (NOC) from college", "required": True, "action_ids": ["a1", "a4"], "confidence": "high", "evidence": "A no-objection letter from your college (NOC)"},
        {"item": "Originals of all listed documents (for joining day)", "required": True, "action_ids": ["a5"], "confidence": "high", "evidence": "carry the originals of all the documents listed above"},
    ],
    "risks": [
        {"description": "Missing the 24-hour window may affect the offer, but the email does not say what happens.", "severity": "high", "stated_in_source": False, "confidence": "low", "evidence": None},
        {"description": "The NOC needs a college officer's signature and may not be obtainable within 24 hours.", "severity": "high", "stated_in_source": False, "confidence": "low", "evidence": None},
    ],
    "questions": [
        {"question": "Can the NOC be sent after the 24-hour window?", "reason": "The email asks for every attachment with the signed letter, but the NOC needs college sign-off."},
        {"question": "What happens if the 24-hour window is missed?", "reason": "The email states no consequence."},
        {"question": "When exactly does the 24-hour window start?", "reason": "It is counted from receiving the email; the receipt time is not in the text."},
    ],
    "confidence": "medium",
    "verification_notes": ["Consequence of missing the 24-hour window is not stated in the source."],
}
OFFER_P = {
    "ordered_action_ids": ["a1", "a2", "a3", "a4", "a5"],
    "dependencies": [
        {"from_action_id": "a1", "to_action_id": "a4", "reason": "The NOC must be attached to the return email."},
        {"from_action_id": "a2", "to_action_id": "a4", "reason": "ID and marksheet must be attached."},
        {"from_action_id": "a3", "to_action_id": "a4", "reason": "The letter must be signed before it is returned."},
        {"from_action_id": "a4", "to_action_id": "a5", "reason": "The offer should be accepted before joining."},
    ],
    "minimum_path": ["a1", "a2", "a3", "a4", "a5"],
    "suggested_prerequisites": [
        {"deadline_id": "d1", "description": "Contact your Training & Placement Officer today to request the NOC.", "reason": "The NOC needs a college signature and is the slowest prerequisite for a 24-hour deadline."}
    ],
    "notes": ["The NOC is likely the bottleneck for the 24-hour window."],
}

# ---------------------------------------------------------------- B: university fee notice
FEE_TEXT = """GREENFIELD INSTITUTE OF TECHNOLOGY
Office of the Controller of Accounts - Notice No. GIT/ACC/2026/0412

Subject: Payment of Semester 5 Tuition Fee

All students of B.Tech Semester 5 are informed that the tuition fee of Rs. 68,500 for the Autumn 2026 semester must be paid on or before {date:+8}.

Payment must be made through the student portal under "Fees > Semester Fee". Students must first clear all library dues and obtain a Library No-Dues Certificate. Students with pending library dues will not be able to generate the fee challan.

After payment, students should upload the payment receipt on the portal and submit a printed copy of the receipt to the Accounts Office (Room 104) by {date:+11}.

A late fee of Rs. 500 per week will be charged for payment made after the due date. Students who have not completed the payment by {date:+22} will not be allowed to appear in the end-semester examinations.

Students who have been awarded a scholarship should email their scholarship sanction letter to accounts@greenfield-demo.example before {date:+5}, so that the fee can be adjusted.

Controller of Accounts
Greenfield Institute of Technology
"""

FEE_U = {
    "title": "Semester 5 tuition fee notice - Greenfield Institute",
    "document_type": "university fee notice",
    "language": "en",
    "summary": "Semester 5 tuition fee of Rs. 68,500 is due on {date:+8}. Library dues must be cleared first, then the receipt uploaded and a printed copy submitted by {date:+11}. Late fees and an exam bar apply.",
    "sensitive_domains": ["financial"],
    "actions": [
        {"id": "a1", "title": "Clear library dues and get the Library No-Dues Certificate", "description": "Required before the fee challan can be generated.", "owner": "You", "priority": "high", "effort_minutes": 45, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "Students must first clear all library dues and obtain a Library No-Dues Certificate."},
        {"id": "a2", "title": "Generate the fee challan on the student portal", "description": "Use the student portal under Fees > Semester Fee.", "owner": "You", "priority": "high", "effort_minutes": 10, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "Payment must be made through the student portal under \"Fees > Semester Fee\"."},
        {"id": "a3", "title": "Pay the Rs. 68,500 tuition fee", "description": "Pay through the student portal.", "owner": "You", "priority": "high", "effort_minutes": 15, "due_at": "{iso:+8}", "can_delegate": None, "confidence": "high", "evidence": "the tuition fee of Rs. 68,500 for the Autumn 2026 semester must be paid on or before {date:+8}"},
        {"id": "a4", "title": "Upload the payment receipt on the portal", "description": "Upload after payment.", "owner": "You", "priority": "medium", "effort_minutes": 5, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "students should upload the payment receipt on the portal"},
        {"id": "a5", "title": "Submit a printed receipt to the Accounts Office (Room 104)", "description": "Hand over a printed copy of the receipt.", "owner": "You", "priority": "medium", "effort_minutes": 20, "due_at": "{iso:+11}", "can_delegate": None, "confidence": "high", "evidence": "submit a printed copy of the receipt to the Accounts Office (Room 104) by {date:+11}"},
        {"id": "a6", "title": "Email scholarship sanction letter to Accounts (only if you hold a scholarship)", "description": "So the fee can be adjusted.", "owner": "You (scholarship holders only)", "priority": "medium", "effort_minutes": 10, "due_at": "{iso:+5}", "can_delegate": None, "confidence": "high", "evidence": "should email their scholarship sanction letter to accounts@greenfield-demo.example before {date:+5}"},
    ],
    "deadlines": [
        {"id": "d1", "label": "Scholarship letter to Accounts", "due_at": "{iso:+5}", "date_text": "before {date:+5}", "relative_hours": None, "kind": "hard", "action_ids": ["a6"], "confidence": "high", "evidence": "before {date:+5}, so that the fee can be adjusted"},
        {"id": "d2", "label": "Tuition fee payment", "due_at": "{iso:+8}", "date_text": "on or before {date:+8}", "relative_hours": None, "kind": "hard", "action_ids": ["a3"], "confidence": "high", "evidence": "must be paid on or before {date:+8}"},
        {"id": "d3", "label": "Printed receipt submitted to Accounts Office", "due_at": "{iso:+11}", "date_text": "by {date:+11}", "relative_hours": None, "kind": "hard", "action_ids": ["a5"], "confidence": "high", "evidence": "(Room 104) by {date:+11}"},
        {"id": "d4", "label": "Exam eligibility cut-off", "due_at": "{iso:+22}", "date_text": "{date:+22}", "relative_hours": None, "kind": "hard", "action_ids": ["a3"], "confidence": "high", "evidence": "have not completed the payment by {date:+22} will not be allowed to appear in the end-semester examinations"},
    ],
    "requirements": [
        {"item": "Library No-Dues Certificate", "required": True, "action_ids": ["a1", "a2"], "confidence": "high", "evidence": "obtain a Library No-Dues Certificate"},
        {"item": "Payment receipt (digital and printed)", "required": True, "action_ids": ["a4", "a5"], "confidence": "high", "evidence": "upload the payment receipt on the portal and submit a printed copy of the receipt"},
        {"item": "Scholarship sanction letter (if awarded a scholarship)", "required": False, "action_ids": ["a6"], "confidence": "high", "evidence": "email their scholarship sanction letter to accounts@greenfield-demo.example"},
    ],
    "risks": [
        {"description": "Late fee of Rs. 500 per week for payment after the due date.", "severity": "medium", "stated_in_source": True, "confidence": "high", "evidence": "A late fee of Rs. 500 per week will be charged for payment made after the due date."},
        {"description": "No exam entry for end-semester examinations if payment is not completed by the cut-off.", "severity": "high", "stated_in_source": True, "confidence": "high", "evidence": "will not be allowed to appear in the end-semester examinations"},
        {"description": "Pending library dues block generation of the fee challan.", "severity": "medium", "stated_in_source": True, "confidence": "high", "evidence": "Students with pending library dues will not be able to generate the fee challan."},
    ],
    "questions": [
        {"question": "Do you hold a scholarship that needs the sanction letter sent?", "reason": "That step applies only to scholarship holders."},
        {"question": "Is a printed receipt still needed if the portal upload succeeds?", "reason": "The notice asks for both."},
    ],
    "confidence": "high",
    "verification_notes": [],
}
FEE_P = {
    "ordered_action_ids": ["a6", "a1", "a2", "a3", "a4", "a5"],
    "dependencies": [
        {"from_action_id": "a1", "to_action_id": "a2", "reason": "Pending library dues block challan generation."},
        {"from_action_id": "a2", "to_action_id": "a3", "reason": "The challan is needed to pay."},
        {"from_action_id": "a3", "to_action_id": "a4", "reason": "The receipt exists only after payment."},
        {"from_action_id": "a4", "to_action_id": "a5", "reason": "The printed receipt comes from the same payment receipt."},
        {"from_action_id": "a6", "to_action_id": "a3", "reason": "The fee is adjusted for scholarship holders before payment."},
    ],
    "minimum_path": ["a1", "a2", "a3", "a4", "a5"],
    "suggested_prerequisites": [
        {"deadline_id": "d2", "description": "Visit the library first and ask how long the No-Dues Certificate takes.", "reason": "It gates the challan and therefore the payment."}
    ],
    "notes": ["The scholarship step is on the critical path only if you hold a scholarship."],
}

# ---------------------------------------------------------------- C: business renewal
LICENCE_TEXT = """ROSEHILL MUNICIPAL CORPORATION - Trade Licence Department
Reminder Notice: Renewal of Trade Licence (Licence No. TL-55102, Ref: RMC/TL/RENEW/2026/2290)

To: The Proprietor, Sunrise Bakery & Cafe

Your Trade Licence TL-55102 expires on {date:+20}. To continue operating without interruption, you must submit a renewal application on or before {date:+13}.

Documents required:
- Renewal application form TL-3 (signed by the proprietor)
- Copy of the current Trade Licence
- Fire safety certificate valid for at least 6 months beyond the renewal date
- Property tax receipt for the current financial year
- Renewal fee of Rs. 4,200 payable by demand draft in favour of "Rosehill Municipal Corporation"

Applications may be submitted online or at Counter 3 of the Trade Licence Department between 10:00 AM and 4:00 PM on working days. A health inspection will be scheduled within 10 working days of submitting a complete application.

Applications received after {date:+13} will attract a penalty of 25% of the renewal fee.

Note: If the fire safety certificate has expired, it must be renewed from the Fire Department before the renewal application is filed.
"""

LICENCE_U = {
    "title": "Trade licence renewal - Sunrise Bakery & Cafe",
    "document_type": "business renewal notice",
    "language": "en",
    "summary": "Trade Licence TL-55102 expires on {date:+20}. A complete renewal application with five documents must be filed by {date:+13} to avoid a 25% penalty; a health inspection follows.",
    "sensitive_domains": ["government", "legal"],
    "actions": [
        {"id": "a1", "title": "Check the fire safety certificate; renew it if expired or under 6 months validity", "description": "It must be valid at least 6 months beyond the renewal date; renew from the Fire Department before filing if expired.", "owner": "You (proprietor)", "priority": "high", "effort_minutes": None, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "If the fire safety certificate has expired, it must be renewed from the Fire Department before the renewal application is filed."},
        {"id": "a2", "title": "Get the property tax receipt for the current financial year", "description": "Needed as an attachment.", "owner": "You", "priority": "medium", "effort_minutes": 30, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "Property tax receipt for the current financial year"},
        {"id": "a3", "title": "Prepare a Rs. 4,200 demand draft to Rosehill Municipal Corporation", "description": "Renewal fee payable by demand draft.", "owner": "You", "priority": "high", "effort_minutes": 60, "due_at": None, "can_delegate": None, "confidence": "high", "evidence": "Renewal fee of Rs. 4,200 payable by demand draft in favour of \"Rosehill Municipal Corporation\""},
        {"id": "a4", "title": "Fill and sign renewal form TL-3; copy the current licence", "description": "Form must be signed by the proprietor.", "owner": "You (proprietor must sign)", "priority": "high", "effort_minutes": 30, "due_at": None, "can_delegate": False, "confidence": "high", "evidence": "Renewal application form TL-3 (signed by the proprietor)"},
        {"id": "a5", "title": "Submit the renewal application (online or Counter 3)", "description": "Counter 3, 10:00 AM-4:00 PM on working days, or online.", "owner": "You", "priority": "high", "effort_minutes": 60, "due_at": "{iso:+13}", "can_delegate": None, "confidence": "high", "evidence": "you must submit a renewal application on or before {date:+13}"},
        {"id": "a6", "title": "Prepare for the health inspection", "description": "Scheduled within 10 working days of a complete application.", "owner": "You", "priority": "medium", "effort_minutes": None, "due_at": None, "can_delegate": None, "confidence": "medium", "evidence": "A health inspection will be scheduled within 10 working days of submitting a complete application."},
    ],
    "deadlines": [
        {"id": "d1", "label": "Renewal application filing deadline", "due_at": "{iso:+13}", "date_text": "on or before {date:+13}", "relative_hours": None, "kind": "hard", "action_ids": ["a5"], "confidence": "high", "evidence": "you must submit a renewal application on or before {date:+13}"},
        {"id": "d2", "label": "Licence expiry", "due_at": "{iso:+20}", "date_text": "{date:+20}", "relative_hours": None, "kind": "event", "action_ids": [], "confidence": "high", "evidence": "Your Trade Licence TL-55102 expires on {date:+20}."},
    ],
    "requirements": [
        {"item": "Renewal form TL-3, signed by the proprietor", "required": True, "action_ids": ["a4", "a5"], "confidence": "high", "evidence": "Renewal application form TL-3 (signed by the proprietor)"},
        {"item": "Copy of the current Trade Licence", "required": True, "action_ids": ["a4", "a5"], "confidence": "high", "evidence": "Copy of the current Trade Licence"},
        {"item": "Fire safety certificate valid 6+ months beyond renewal date", "required": True, "action_ids": ["a1", "a5"], "confidence": "high", "evidence": "Fire safety certificate valid for at least 6 months beyond the renewal date"},
        {"item": "Property tax receipt (current financial year)", "required": True, "action_ids": ["a2", "a5"], "confidence": "high", "evidence": "Property tax receipt for the current financial year"},
        {"item": "Renewal fee Rs. 4,200 by demand draft", "required": True, "action_ids": ["a3", "a5"], "confidence": "high", "evidence": "Renewal fee of Rs. 4,200 payable by demand draft"},
    ],
    "risks": [
        {"description": "Late applications attract a penalty of 25% of the renewal fee.", "severity": "medium", "stated_in_source": True, "confidence": "high", "evidence": "Applications received after {date:+13} will attract a penalty of 25% of the renewal fee."},
        {"description": "Operations may be interrupted if the licence lapses.", "severity": "high", "stated_in_source": True, "confidence": "medium", "evidence": "To continue operating without interruption"},
    ],
    "questions": [
        {"question": "Is the current fire safety certificate valid for 6+ months beyond the renewal date?", "reason": "If not, it must be renewed first, which adds a dependency before filing."},
        {"question": "Is the demand-draft fee affected by the penalty if filing is late?", "reason": "The notice gives the penalty rate but not how it is collected."},
    ],
    "confidence": "high",
    "verification_notes": [],
}
LICENCE_P = {
    "ordered_action_ids": ["a1", "a2", "a3", "a4", "a5", "a6"],
    "dependencies": [
        {"from_action_id": "a1", "to_action_id": "a5", "reason": "The certificate must be valid before filing."},
        {"from_action_id": "a2", "to_action_id": "a5", "reason": "Property tax receipt is a required attachment."},
        {"from_action_id": "a3", "to_action_id": "a5", "reason": "The demand draft is part of the application."},
        {"from_action_id": "a4", "to_action_id": "a5", "reason": "The signed form is part of the application."},
        {"from_action_id": "a5", "to_action_id": "a6", "reason": "The inspection follows a complete application."},
    ],
    "minimum_path": ["a1", "a2", "a3", "a4", "a5"],
    "suggested_prerequisites": [
        {"deadline_id": "d1", "description": "Confirm the fire safety certificate's expiry date today.", "reason": "If it must be renewed, that step has its own lead time before filing."}
    ],
    "notes": ["Filing is blocked until all five documents are ready."],
}

SAMPLES = [
    {"id": "offer", "ref": "OFFER-7781", "label": "Internship offer email", "blurb": "Sign and return within 24 hours", "text": OFFER_TEXT, "u": OFFER_U, "p": OFFER_P},
    {"id": "fee", "ref": "GIT/ACC/2026/0412", "label": "University fee notice", "blurb": "Payment deadline + required steps", "text": FEE_TEXT, "u": FEE_U, "p": FEE_P},
    {"id": "licence", "ref": "RMC/TL/RENEW/2026/2290", "label": "Business licence renewal", "blurb": "Deadline + documents required", "text": LICENCE_TEXT, "u": LICENCE_U, "p": LICENCE_P},
]


def list_samples(today: date):
    return [
        {"id": s["id"], "label": s["label"], "blurb": s["blurb"], "text": render(s["text"], today)}
        for s in SAMPLES
    ]


def find_by_text(text: str):
    for s in SAMPLES:
        if s["ref"] in text:
            return s
    return None
