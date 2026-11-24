"""Narration script. Each scene -> list of sentences.
A sentence is a list of chunks (caption_html, spoken_text). The spoken parts of a
sentence are joined and synthesised as one utterance so prosody stays natural;
caption chunks are timed from the word boundaries.
<b>..</b> marks the highlighted words in a caption.
A caption of "+" keeps the previous caption on screen; "" shows none.
A sentence may be a dict {"voice": "avatar", "chunks": [...]} for the kiosk avatar line.
"""

SCENES = [
    ("intro", [
        [("Chat360 · <b>Agentic AI</b> for Insurance", "Chat three sixty: Agentic A I for insurance.")],
    ]),
    ("words", [
        [("Quote. Claim. Renew. Protect.", "Quote.")], [("+", "Claim.")], [("+", "Renew.")], [("+", "Protect.")],
    ]),
    ("hero", [
        [("See how Chat360 <b>Agentic AI</b> runs the entire insurance journey,",
          "See how Chat three sixty Agentic A I runs the entire insurance journey,"),
         ("end to end, for life, general and health insurers.",
          "end to end, for life, general, and health insurers.")],
    ]),
    ("seven", [
        [("<b>Seven modules.</b> One platform.", "Seven modules. One platform.")],
    ]),
    ("health", [
        [("Start with <b>Insure360</b>.", "Start with Insure three sixty.")],
        [("A customer is admitted to hospital", "A customer is admitted to hospital"),
         ("and asks for a <b>cashless claim</b> on WhatsApp.", "and asks for a cashless claim on WhatsApp.")],
        [("Insure360 <b>fetches the policy</b> from the phone number,",
          "Insure three sixty fetches the policy from the phone number,"),
         ("<b>checks eligibility,</b>", "checks eligibility,"),
         ("and sends the pre-authorisation request to the insurer.",
          "and sends the pre-authorisation request to the insurer.")],
        [("The insurer approves <b>₹45,000</b>.", "The insurer approves forty-five thousand rupees.")],
        [("At discharge, the customer pays only their share —", "At discharge, the customer pays only their share,"),
         ("<b>₹7,150</b> at the desk.", "seven thousand, one hundred and fifty rupees at the desk.")],
        [("<b>Cashless</b>, from request to discharge.", "Cashless, from request to discharge.")],
    ]),
    ("motor", [
        [("Now, a <b>motor claim</b>.", "Now, a motor claim.")],
        [("The customer sends a photo of the damaged car", "The customer sends a photo of the damaged car"),
         ("and asks for <b>cashless at a garage</b>.", "and asks for cashless at a garage.")],
        [("Instantly, Insure360 <b>creates a claim group</b>", "Instantly, Insure three sixty creates a claim group,"),
         ("with the customer, the service centre,", "with the customer, the service centre,"),
         ("the insurance desk and the insurer, in one chat.", "the insurance desk, and the insurer, in one chat.")],
        [("<b>RM360</b> assesses the photo:", "R M three sixty assesses the photo."),
         ("front bumper and headlamp, <b>₹42,600</b>.",
          "Front bumper and headlamp, forty-two thousand six hundred rupees.")],
        [("A <b>surveyor joins</b> the group and the estimate is approved.",
          "A surveyor joins the group, and the estimate is approved.")],
        [("When the car is ready, the insurer pays the garage <b>₹36,200</b>,",
          "When the car is ready, the insurer pays the garage thirty-six thousand two hundred rupees,"),
         ("and the customer pays just <b>₹6,400</b>.", "and the customer pays just six thousand four hundred.")],
        [("<b>One group.</b> Everyone aligned.", "One group. Everyone aligned.")],
    ]),
    ("rm", [
        [("<b>RM360</b> keeps the whole quote journey inside WhatsApp.",
          "R M three sixty keeps the whole quote journey inside WhatsApp.")],
        [("It compares plans, answers rider questions,", "It compares plans, answers rider questions,"),
         ("and completes <b>CKYC in 2 seconds</b>.", "and completes C K Y C in two seconds.")],
        [("If a buyer drops off,", "If a buyer drops off,"),
         ("a <b>nudge</b> brings them back to the exact step.", "a nudge brings them back to the exact step.")],
        [("That's a <b>25–35% uplift</b> in quote-to-bind.",
          "That's a twenty-five to thirty-five percent uplift in quote to bind.")],
    ]),
    ("engage", [
        [("<b>Engage360</b> puts renewals on autopilot.", "Engage three sixty puts renewals on autopilot.")],
        [("A reminder goes out before the premium is due.", "A reminder goes out before the premium is due.")],
        [("If the customer doesn't act,", "If the customer doesn't act,"),
         ("<b>Voice AI</b> calls in their <b>regional language</b>", "Voice A I calls in their regional language,"),
         ("and handles objections with empathy.", "and handles objections with empathy.")],
        [("The <b>payment link</b> lands on WhatsApp", "The payment link lands on WhatsApp"),
         ("while the customer is still on the call.", "while the customer is still on the call.")],
        [("They can even <b>pay in two parts</b>,", "They can even pay in two parts,"),
         ("and AutoPay keeps the policy active.", "and AutoPay keeps the policy active.")],
    ]),
    ("workforce", [
        [("<b>Workforce360</b> is a co-pilot for bank RMs, agents and POSPs.",
          "Workforce three sixty is a co-pilot for bank R Ms, agents, and P O S Ps.")],
        [("One voice note returns <b>accurate quotes</b>", "One voice note returns accurate quotes,"),
         ("and a co-branded PDF, ready to share.", "and a co-branded P D F, ready to share.")],
        [("It closes training gaps by <b>coaching advisors</b>", "It closes training gaps by coaching advisors"),
         ("on riders, underwriting rules and how to pitch them.",
          "on riders, underwriting rules, and how to pitch them.")],
        [("And every lead is <b>logged in Salesforce</b>, automatically.",
          "And every lead is logged in Salesforce, automatically.")],
    ]),
    ("agent", [
        [("<b>Agent360</b> gives managers full visibility of the team.",
          "Agent three sixty gives managers full visibility of the team.")],
        [("Live conversations, workloads and response times, in one view.",
          "Live conversations, workloads, and response times, in one view.")],
        [("So <b>nothing slips through</b>.", "So nothing slips through.")],
    ]),
    ("pivc", [
        [("For compliance,", "For compliance,"),
         ("<b>Insure360</b> runs the pre-issuance verification call.",
          "Insure three sixty runs the pre-issuance verification call.")],
        [("It clarifies terms like the lock-in", "It clarifies terms like the lock-in,"),
         ("and <b>flags mis-selling risk</b> for review,", "and flags mis-selling risk for review,"),
         ("with a <b>timestamped transcript</b> for audit.", "with a timestamped transcript for audit.")],
    ]),
    ("kiosk", [
        [("In the branch, the <b>Avatar Kiosk</b>", "In the branch, the Avatar Kiosk"),
         ("answers policy questions face-to-face.", "answers policy questions face to face.")],
        {"voice": "avatar", "chunks": [
            ("<i>Avatar:</i> “Congratulations! You can add your baby",
             "Congratulations! You can add your baby"),
            ("to your health policy mid-term.", "to your health policy mid-term."),
            ("You’ll just need the birth certificate and the endorsement form.”",
             "You'll just need the birth certificate, and the endorsement form.")]},
        [("It handles <b>endorsements</b> instantly.", "It handles endorsements instantly.")],
        [("And <b>one scan</b> continues the session on WhatsApp —", "And one scan continues the session on WhatsApp,"),
         ("a <b>24/7 concierge</b> at every branch.", "a twenty-four seven concierge at every branch.")],
    ]),
    ("reach", [
        [("<b>Reach360</b> helps insurers build", "Reach three sixty helps insurers build"),
         ("a stronger digital presence and customer trust.", "a stronger digital presence, and customer trust.")],
        [("It automates customer <b>review management</b>,", "It automates customer review management,"),
         ("manages <b>Google Business profiles</b>,", "manages Google Business profiles,"),
         ("and strengthens social media presence,", "and strengthens social media presence,"),
         ("helping insurers stay <b>visible, credible and connected</b> with customers.",
          "helping insurers stay visible, credible, and connected with customers.")],
    ]),
    ("hub", [
        [("Every module runs on <b>one Agentic AI platform</b>,", "Every module runs on one Agentic A I platform,"),
         ("sharing context across every channel.", "sharing context across every channel.")],
    ]),
    ("proof", [
        [("<b>Chola MS</b> collected ₹1.7 crore in premium", "Chola M S collected one point seven crore rupees in premium,"),
         ("through WhatsApp payments, in just three months,", "through WhatsApp payments, in just three months,"),
         ("and over <b>400 brands</b> already use Chat360.",
          "and over four hundred brands already use Chat three sixty.")],
    ]),
    ("cta", [
        [("Ready to put <b>Agentic AI</b> to work in insurance?", "Ready to put Agentic A I to work in insurance?")],
        [("Scan the QR code, or visit <b>Chat360.ai</b> to book a demo.",
          "Scan the Q R code, or visit Chat three sixty dot A I, to book a demo.")],
    ]),
    ("end", [
        [("", "Chat three sixty."),
         ("", "One omnichannel Agentic A I platform, for every insurance journey.")],
    ]),
]
