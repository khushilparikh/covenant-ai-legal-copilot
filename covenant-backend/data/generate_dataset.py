"""
Generates a synthetic-but-realistic labeled dataset of contract clause
sentences for training the clause classification model.

Each clause type has multiple sentence templates with swappable fillers,
producing varied, non-duplicate training examples that mimic the phrasing
patterns found in real commercial contracts (MSAs, NDAs, vendor agreements,
employment contracts, leases).
"""
import csv
import itertools
import random

random.seed(42)

PARTIES = ["Client", "Vendor", "Company", "Contractor", "Licensee", "Licensor",
           "Employer", "Employee", "Tenant", "Landlord", "Disclosing Party", "Receiving Party"]
PERIODS = ["thirty (30) days", "sixty (60) days", "ninety (90) days", "fifteen (15) days",
           "forty-five (45) days", "twelve (12) months", "twenty-four (24) months", "one (1) year"]
AMOUNTS = ["the total Fees paid in the preceding twelve (12) months", "$500,000", "the Contract Value",
           "the Fees paid in the preceding six (6) months", "$1,000,000 USD", "the Annual Contract Value"]
JURISDICTIONS = ["the State of Delaware", "the State of New York", "England and Wales",
                 "the Republic of India", "the State of California", "Singapore"]

TEMPLATES = {
    "Confidentiality": [
        "{a} shall hold in strict confidence all Confidential Information disclosed by {b} and shall not disclose such information to any third party without prior written consent.",
        "Each party agrees to protect the other party's Confidential Information using no less than a reasonable degree of care, and in no event less care than it uses to protect its own confidential materials.",
        "{a} shall not use the Confidential Information of {b} for any purpose other than performing its obligations under this Agreement.",
        "The obligations of confidentiality set forth in this Section shall survive termination of this Agreement for a period of {p}.",
        "Confidential Information shall not include information that is or becomes publicly available through no fault of the Receiving Party.",
        "{a} shall limit access to Confidential Information to employees and contractors who have a legitimate need to know such information.",
        "Upon termination of this Agreement, {a} shall promptly return or destroy all copies of Confidential Information belonging to {b}.",
    ],
    "Termination": [
        "Either party may terminate this Agreement upon {p} prior written notice to the other party.",
        "{a} may terminate this Agreement immediately upon written notice if {b} commits a material breach that remains uncured for {p} following notice thereof.",
        "This Agreement shall automatically terminate upon the expiration of the Term unless renewed in accordance with Section 2.",
        "{a} may terminate this Agreement for convenience by providing {p} written notice, without cause or penalty.",
        "Upon termination, {b} shall immediately cease use of all Services and return any Company property in its possession.",
        "In the event of termination, {a} shall remain liable for all Fees accrued through the effective date of termination.",
        "Either party may terminate this Agreement immediately if the other party becomes insolvent or files for bankruptcy protection.",
    ],
    "Liability": [
        "{a}'s aggregate liability under this Agreement shall not exceed {am}.",
        "In no event shall either party be liable to the other for any indirect, incidental, special, or consequential damages arising out of this Agreement.",
        "The limitation of liability set forth in this Section shall not apply in cases of gross negligence, willful misconduct, or fraud.",
        "{a} disclaims all warranties, express or implied, including any implied warranties of merchantability or fitness for a particular purpose.",
        "Neither party's liability shall be limited with respect to breaches of confidentiality obligations or infringement of intellectual property rights.",
        "{b}'s total liability arising from this Agreement, whether in contract, tort, or otherwise, shall not exceed {am}.",
    ],
    "Indemnification": [
        "{a} shall indemnify, defend, and hold harmless {b} from and against any third-party claims, damages, or expenses arising from {a}'s breach of this Agreement.",
        "{a} agrees to indemnify {b} against any claims arising from {a}'s negligence, willful misconduct, or violation of applicable law.",
        "The indemnifying party shall have the right to control the defense and settlement of any indemnified claim, subject to the indemnified party's approval.",
        "{a} shall reimburse {b} for reasonable attorneys' fees and costs incurred in defending against any indemnified claim.",
        "This indemnification obligation shall survive termination or expiration of this Agreement.",
        "{b} shall promptly notify {a} in writing of any claim for which indemnification is sought under this Section.",
    ],
    "Payment": [
        "{a} shall pay all undisputed invoices within {p} of receipt of a valid invoice from {b}.",
        "All Fees are due and payable in advance on a monthly basis, and are non-refundable except as expressly provided herein.",
        "Late payments shall accrue interest at a rate of 1.5% per month or the maximum rate permitted by applicable law, whichever is lower.",
        "{b} shall invoice {a} monthly in arrears for Services rendered during the preceding calendar month.",
        "{a} is responsible for all applicable taxes, duties, and government charges, excluding taxes based on {b}'s net income.",
        "Any disputed invoice amounts shall be resolved in accordance with the dispute resolution procedure set forth in Section 12.",
    ],
    "Intellectual_Property": [
        "All intellectual property rights in the Deliverables shall vest in {a} upon full payment of all applicable Fees.",
        "{b} grants {a} a non-exclusive, non-transferable license to use the Licensed Materials solely for internal business purposes.",
        "Each party retains ownership of its pre-existing intellectual property and any improvements thereto developed independently.",
        "{a} shall retain all right, title, and interest in and to its trademarks, trade names, and logos.",
        "Any work product created by {b} specifically for {a} under this Agreement shall be considered a work made for hire.",
        "{b} represents and warrants that the Deliverables do not infringe upon the intellectual property rights of any third party.",
    ],
    "Force_Majeure": [
        "Neither party shall be liable for any failure or delay in performance due to causes beyond its reasonable control, including acts of God, war, or natural disaster.",
        "A Force Majeure Event shall not include failures caused by a party's financial condition or negligence.",
        "The party affected by a Force Majeure Event shall notify the other party within {p} of the event's occurrence and use commercially reasonable efforts to mitigate its impact.",
        "If a Force Majeure Event continues for more than {p}, either party may terminate this Agreement upon written notice.",
        "Performance obligations suspended due to a Force Majeure Event shall resume promptly once the event has ceased.",
    ],
    "Non_Compete": [
        "{b} agrees not to engage in any business that directly competes with {a} within the Territory during the Term and for {p} thereafter.",
        "During the term of employment and for {p} following termination, Employee shall not solicit any customers or employees of {a}.",
        "This non-compete restriction shall be limited to the geographic area in which {a} actively conducts business.",
        "{b} acknowledges that the restrictions in this Section are reasonable and necessary to protect {a}'s legitimate business interests.",
        "Any breach of this non-compete provision shall entitle {a} to seek injunctive relief in addition to monetary damages.",
    ],
    "Arbitration": [
        "Any dispute arising out of or relating to this Agreement shall be resolved through binding arbitration administered in accordance with the rules of the relevant arbitral institution.",
        "The arbitration shall be conducted by a single arbitrator and the seat of arbitration shall be {j}.",
        "The parties agree to waive their right to a jury trial and to resolve all disputes exclusively through arbitration.",
        "Prior to initiating arbitration, the parties shall attempt in good faith to resolve the dispute through informal negotiation for a period of {p}.",
        "The arbitrator's decision shall be final and binding, and judgment may be entered in any court of competent jurisdiction.",
    ],
    "Data_Privacy": [
        "{a} shall process Personal Data solely in accordance with the Data Processing Addendum and applicable data protection laws.",
        "{a} shall implement appropriate technical and organizational measures to protect Personal Data against unauthorized access or disclosure.",
        "{a} shall notify {b} of any Personal Data Breach without undue delay and in any event within {p} of becoming aware of it.",
        "{b} shall not transfer Personal Data outside the approved jurisdictions without {a}'s prior written consent and appropriate safeguards.",
        "Upon termination of this Agreement, {a} shall delete or return all Personal Data processed on behalf of {b}, unless retention is required by law.",
    ],
    "General": [
        "This Agreement constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements.",
        "This Agreement shall be governed by and construed in accordance with the laws of {j}, without regard to its conflict of laws principles.",
        "No amendment or modification of this Agreement shall be effective unless made in writing and signed by both parties.",
        "If any provision of this Agreement is held to be invalid or unenforceable, the remaining provisions shall continue in full force and effect.",
        "Neither party may assign this Agreement without the prior written consent of the other party, except in connection with a merger or acquisition.",
        "The relationship between the parties is that of independent contractors, and nothing herein shall be construed as creating a partnership or joint venture.",
        "Any notice required under this Agreement shall be in writing and delivered by email, courier, or certified mail to the address specified above.",
    ],
}


def fill(template):
    a, b = random.sample(PARTIES, 2)
    return template.format(
        a=a, b=b,
        p=random.choice(PERIODS),
        am=random.choice(AMOUNTS),
        j=random.choice(JURISDICTIONS),
    )


def generate(n_per_class=32):
    rows = []
    for label, templates in TEMPLATES.items():
        combos = set()
        attempts = 0
        while len(combos) < n_per_class and attempts < n_per_class * 8:
            t = random.choice(templates)
            sentence = fill(t)
            combos.add(sentence)
            attempts += 1
        for s in combos:
            rows.append((s, label))
    random.shuffle(rows)
    return rows


if __name__ == "__main__":
    rows = generate(n_per_class=32)
    with open("clause_training_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(rows)
    print(f"Generated {len(rows)} labeled clause examples across {len(TEMPLATES)} classes.")
