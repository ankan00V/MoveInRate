"""Complaint taxonomy for MoveInSync Play Store reviews.

Built by reading ~400 recent 1-2 star reviews by hand, then encoding each theme as
regex patterns (English + common Hinglish spellings). Deterministic and free to run,
so it can be re-run on every scheduled fetch. A review can carry several themes.
Validated against a hand-labelled sample (see README / methodology).

`owner` says who can fix it:
  app   -> Product / Engineering (the app itself)
  ops   -> Operations / vendor / client transport desk (the ride, not the app)
"""
import re

THEMES = {
    # ---------------- APP (Product / Engineering) ----------------
    "login_otp_session": dict(
        owner="app", label="Login, OTP & forced logouts",
        pattern=r"log ?in|logs? ?out|logged out|logouting|sign ?in|signs? ?out|signed out|sign ?up|session expired|unauthori[sz]ed|\bsso\b|"
                r"otp (is )?(not|n't|never|nahi|nhi)|not (getting|receiving|received|get|coming)[a-z ]{0,20}otp|otp[a-z ']{0,25}(not|never|n't) (received|come|coming|sent|generat)|"
                r"no otp|otp (verification|challenge)|re-?login|every ?time[a-z ]{0,30}otp|register|registration|verif(y|ication) (code|otp)|can'?t (access|login)|"
                r"(get|getting|receiv\w*|send\w*|generat\w*|coming|asks? for|access)[a-z ']{0,20}otp|otp[a-z ']{0,20}(send|sent|generat|function|down)|couldn'?t (able to )?access|"
                r"validate identity|too secure|verify via|otp chall[ae]nge|authenticat",
    ),
    "crash_not_opening": dict(
        owner="app", label="Crashes, won't open, slow / blank screen",
        pattern=r"crash|not open|doesn'?t open|does not open|won'?t open|not opening|unable to open|can'?t open|blank|white screen|"
                r"hang|stuck|freez|\blag|slow|load(ing)?|takes? (too much|long|eternity)|server (is )?down|not (working|responding)|doesn'?t work|"
                r"does not work|isn'?t working|404|error|glitch|\bbug|keeps? (closing|stopping)|automatic(ally)? close|"
                r"doens'?t work|\bdown\b|not stable|unstable|unreliable|app issue|getting stopped|closes as soon|stopped working",
    ),
    "play_integrity_reinstall": dict(
        owner="app", label="'Not installed from Play Store' / forced reinstall",
        pattern=r"(installed|downloaded)[a-z ]{0,10}(from|thru|through|via) (the )?play ?store|reinstall|re-install|uninstall|keeps? uninstalling|download(ed)? it again",
    ),
    "forced_prompts": dict(
        owner="app", label="Forced trip rating, review nags, policy re-accept, permissions, banners",
        pattern=r"forc(ed|ing)[a-z ]{0,20}(rat|review|feedback)|rate every|rating after every|after every (ride|trip)|no (option to )?skip|skip (option|rating|button)|"
                r"option (of|to) skip|mandatory (review|rating|feedback)|play ?store review|asks? (for )?(a )?(review|rating)|"
                r"(policy|policies|agreement|terms|disclaimer|consent)[^.]{0,60}(every ?time|again|each time|repeated)|every ?time[^.]{0,60}(policy|agree|accept|disclaimer)|"
                r"skip rating|star pop|permission|time ?zone|clock setting|banner|pop.?up|seat ?belt|\bads?\b|advertis",
    ),
    "tracking_eta": dict(
        owner="app", label="Live tracking, GPS, ETA & location accuracy",
        pattern=r"track|gps|\beta\b|live location|wrong location|location (is )?(wrong|incorrect|inaccurate|not)|\bmap|zoom|arrival time|real ?time|"
                r"co-?passenger|co-?employee|cab ?mates?|location|address",
    ),
    "booking_flow": dict(
        owner="app", label="Booking, cancel, waitlist & schedule flow",
        pattern=r"\bbook|cancel|wait ?list|reschedul|schedule|roster|cut ?off|adhoc|ad-hoc|in advance|am/pm|\bam\b.{0,10}\bpm\b|\bseat\b|date range",
    ),
    "ui_redesign": dict(
        owner="app", label="New UI / update made it harder to use",
        pattern=r"new (ui|update|version|app|design|interface|ux)|recent update|latest update|after (the )?(latest |recent |new )?update|old (version|app|ui)|"
                r"previous (version|app|ui)|bring back|not user ?friendly|user ?unfriendly|\bui\b|\bux\b|interface|confusing|complicated|too many (steps|clicks)",
    ),
    "notifications": dict(
        owner="app", label="Notification spam / wrong notifications",
        pattern=r"notification",
    ),
    "offline_info": dict(
        owner="app", label="Trip details / OTP / cab no. unavailable when needed",
        pattern=r"offline|no network|without internet|lost signal|(can'?t|cannot|not able to|unable to) see[a-z ]{0,30}(otp|cab|trip|detail|number|vehicle)|"
                r"cab (number|no\.?|details?) (is )?not|otp (is )?(not )?(visible|showing|disappear)|no (cab|vehicle) (number|details)",
    ),
    "boarding_qr": dict(
        owner="app", label="Boarding: QR scan & OTP screen",
        pattern=r"\bqr\b|scann|view otp|otp[a-z ]{0,20}(disappear|behind|screen|visible)|board(ing)? otp",
    ),
    "contact_support": dict(
        owner="app", label="Can't reach driver / helpdesk from the app",
        pattern=r"call(ing)? (the )?driver|chat|contact|help ?desk|customer (care|support|service)|support team|\bivr\b|no (one|body) (is )?(respond|help|pick)|"
                r"not reachable|no response|complaint|grievance|escalat|\bcall(ing)?\b",
    ),
    # ---------------- OPS (Operations / vendors / client transport desk) ----------------
    "driver_behaviour": dict(
        owner="ops", label="Driver behaviour & professionalism",
        pattern=r"driver[a-z ]{0,30}(rude|behav|misbehav|abusiv|unprofessional|manner|rash|attitude|shout|drunk|phone)|rude|misbehav|abusive|rash driv|"
                r"unprofessional driver|driving (is )?(rash|bad|dangerous)",
    ),
    "punctuality_noshow": dict(
        owner="ops", label="Late cabs, no-shows, cab not assigned",
        pattern=r"\blate\b|delay|no ?show|not on time|on time|never on time|wait(ed|ing)? (for )?\d|waiting|(cab|vehicle|driver) (did ?n'?t|didn'?t|not|never) (come|arrive|reach|turn)|"
                r"not (assigned|allocated|allotted)|allocation|early pick|too early|missed (my|the) (cab|shuttle|bus)|(pick ?up|drop|arriv\w*) tim(e|ing)|pick and drop",
    ),
    "routing_clubbing": dict(
        owner="ops", label="Routing, clubbing, nodal points & trip length",
        pattern=r"\brout(e|es|ing)\b|clubb|sequence|nodal|nodel|nodle|pick ?up point|drop point|detour|long (route|way)|\d+ ?(hr|hour)s? to reach|walk",
    ),
    "safety": dict(
        owner="ops", label="Safety concerns",
        pattern=r"safety|unsafe|not safe|women|harass|security|escort|guard|danger",
    ),
    "service_general": dict(
        owner="ops", label="Transport service / vendor / desk (general)",
        pattern=r"servic|transport (team|desk|department)|cab facility|vendor|management|cab provider|travel desk|\bstaff\b",
    ),
}

COMPILED = {k: re.compile(v["pattern"], re.I) for k, v in THEMES.items()}


def classify(text):
    text = str(text or "")
    tags = [k for k, rx in COMPILED.items() if rx.search(text)]
    return tags or ["unspecified"]


LABELS = {k: v["label"] for k, v in THEMES.items()} | {"unspecified": "Generic (e.g. 'worst app', no detail)"}
OWNER = {k: v["owner"] for k, v in THEMES.items()} | {"unspecified": "-"}
