import os
import random
import pickle
import pandas as pd
from datetime import datetime
import database

# ── Load ML Models ───────────────────────────────────────────
def load_model(name):
    path = os.path.join(os.path.dirname(__file__), 'saved', name)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

MODELS = {
    'CC': load_model('cc_model.pkl'),
    'ML': load_model('ml_model.pkl'),
    'UT': load_model('ut_model.pkl'),
    'FT': load_model('ft_model.pkl'),
    'IT': load_model('it_model.pkl')
}

BANKS = ['HDFC', 'SBI', 'ICICI', 'Axis', 'Kotak',
         'PNB', 'BoB', 'Canara', 'UCO', 'Bandhan']
COUNTRIES = ['IN', 'IN', 'IN', 'IN', 'IN', 'AE', 'US', 'GB', 'CN', 'RU', 'NG']
DEVICES = ['iPhone 15', 'Samsung S24', 'Pixel 8', 'OnePlus 12',
           'Redmi Note 13', 'Desktop Chrome', 'Unknown Device']
FRAUD_TYPES = ['CC', 'ML', 'UT', 'FT', 'IT']


def rand(min_val, max_val):
    return random.random() * (max_val - min_val) + min_val


def randInt(min_val, max_val):
    return random.randint(min_val, max_val)


def pick(arr):
    return random.choice(arr)


def uid():
    return 'TXN' + str(random.randint(0, 999999)).zfill(6)

# ── Risk scoring helpers ─────────────────────────────────────


COUNTRY_RISK = {'IN': 5, 'US': 30, 'GB': 28,
                'AE': 35, 'CN': 60, 'RU': 80, 'NG': 95}


def countryScore(c):
    return COUNTRY_RISK.get(c, 40)


def amountScore(amt, low, high):
    if amt < low:
        return round((amt / low) * 20)
    if amt > high:
        return min(100, round(60 + ((amt - high) / high) * 40))
    return round(20 + ((amt - low) / (high - low)) * 40)


def hourScore(h):
    if 1 <= h <= 4:
        return 85
    if h in (0, 5):
        return 60
    if h >= 22:
        return 45
    return 10


def to_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() == 'true'
    return False

# ── Credit Card Fraud Analyzer ───────────────────────────────


def analyzeCC(p):
    amt = float(p.get('amount', 0) or 0)
    hour = int(p.get('hour', 12) or 12)
    vel = int(p.get('velocity', 1) or 1)
    country = p.get('country', 'IN') or 'IN'
    newDev = to_bool(p.get('newDevice', False))
    foreignIp = to_bool(p.get('foreignIp', False))

    fAmt = amountScore(amt, 5000, 200000)
    fHr = hourScore(hour)
    fVel = min(100, round((vel / 30) * 100))
    fCty = countryScore(country)
    fDev = 75 if newDev else 5
    fFip = 70 if foreignIp else 5

    fFip = 70 if foreignIp else 5

    if MODELS['CC']:
        df = pd.DataFrame([{
            'amount': amt, 'hour': hour, 'velocity': vel,
            'newDevice': 1 if newDev else 0, 'foreignIp': 1 if foreignIp else 0
        }])
        score = min(100, round(MODELS['CC'].predict_proba(df)[0][1] * 100))
    else:
        score = min(100, round(fAmt * 0.25 + fHr * 0.20 + fVel *
                    0.25 + fCty * 0.10 + fDev * 0.10 + fFip * 0.10))

    level = 'CRITICAL' if score >= 75 else 'HIGH' if score >= 50 else 'MEDIUM' if score >= 25 else 'LOW'
    action = 'BLOCK & ALERT' if score >= 75 else 'STEP-UP AUTH' if score >= 50 else 'FLAG FOR REVIEW' if score >= 25 else 'APPROVE'

    messages = {
        'CRITICAL': 'Transaction exhibits multiple high-confidence fraud signals — velocity attack, geo anomaly, and off-hours access combined. Immediate block recommended.',
        'HIGH': 'Elevated fraud risk detected across several factors. Step-up authentication required before processing.',
        'MEDIUM': 'Some suspicious signals present. Transaction flagged for manual review before settlement.',
        'LOW': 'Transaction within normal behavioral parameters. Low fraud probability — approved.'
    }

    steps = {
        'CRITICAL': ['Card immediately blocked across all channels', 'SMS + app alert sent to cardholder', 'OTP challenge issued on all linked devices', 'Case routed to fraud operations team', 'Merchant notified of high-risk transaction'],
        'HIGH': ['Step-up OTP authentication required', 'Card temporarily limited to low-value transactions', 'Transaction held for 60 seconds pending auth', 'Risk score logged for model retraining'],
        'MEDIUM': ['Transaction queued for analyst review', 'Soft limit applied to card for next 24 hours', 'Customer notification sent as precaution'],
        'LOW': ['Transaction approved and settled', 'Behavioral profile updated with this data point', 'No further action required']
    }

    return {
        'score': score,
        'factors': {
            'transactionAmount': {'score': fAmt, 'detail': f"₹{amt:,.2f} — {'high-value transaction' if fAmt >= 60 else 'within normal range'}"},
            'timeOfDay': {'score': fHr, 'detail': f"Hour {hour}:00 — {'peak fraud window (1–4 AM)' if fHr >= 70 else 'normal hours'}"},
            'velocityAnomaly': {'score': fVel, 'detail': f"{vel} transactions this hour — {'far above normal (2–3/hr)' if fVel >= 70 else 'within expected range'}"},
            'geographicRisk': {'score': fCty, 'detail': f"Origin: {country} — risk tier {'CRITICAL' if fCty >= 70 else 'HIGH' if fCty >= 40 else 'LOW'}"},
            'deviceRisk': {'score': fDev, 'detail': 'Unregistered device — first seen today' if newDev else 'Known trusted device'},
            'foreignIpSignal': {'score': fFip, 'detail': 'IP geolocation does not match card country' if foreignIp else 'IP consistent with cardholder location'}
        },
        'verdict': {'level': level, 'action': action, 'message': messages[level], 'steps': steps[level]}
    }


# ── Money Laundering Analyzer ────────────────────────────────

def analyzeML(p):
    amt = float(p.get('amount', 0) or 0)
    txc = int(p.get('txnCount24h', 1) or 1)
    age = int(p.get('accountAgeMonths', 12) or 12)
    country = p.get('country', 'IN') or 'IN'
    cross = to_bool(p.get('crossBorder', False))
    shell = to_bool(p.get('shellCompany', False))
    struct = to_bool(p.get('structuring', False))

    fAmt = 90 if (85000 <= amt <= 99999) else amountScore(amt, 10000, 500000)
    fTxc = min(100, round((txc / 30) * 100))
    fAge = 80 if age <= 3 else 40 if age <= 12 else 10
    fCty = countryScore(country)
    fCross = 65 if cross else 5
    fShell = 90 if shell else 5
    fStruct = 85 if struct else 5

    fShell = 90 if shell else 5
    fStruct = 85 if struct else 5

    if MODELS['ML']:
        df = pd.DataFrame([{
            'amount': amt, 'txnCount24h': txc, 'crossBorder': 1 if cross else 0,
            'shellCompany': 1 if shell else 0, 'structuring': 1 if struct else 0,
            'accountAgeMonths': age
        }])
        score = min(100, round(MODELS['ML'].predict_proba(df)[0][1] * 100))
    else:
        score = min(100, round(
            fAmt * 0.20 + fTxc * 0.15 + fAge * 0.10 + fCty * 0.10 +
            fCross * 0.10 + fShell * 0.20 + fStruct * 0.15))

    level = 'CRITICAL' if score >= 75 else 'HIGH' if score >= 50 else 'MEDIUM' if score >= 25 else 'LOW'
    action = 'FREEZE & FILE STR' if score >= 75 else 'ENHANCED DUE DILIGENCE' if score >= 50 else 'MONITOR & LOG' if score >= 25 else 'CLEAR'

    messages = {
        'CRITICAL': 'Strong money laundering indicators: structuring pattern, shell company beneficiary, and FATF high-risk jurisdiction detected simultaneously. Accounts frozen and STR filed with FIU-IND.',
        'HIGH': 'Multiple AML red flags present. Enhanced due diligence required — transaction held pending compliance review.',
        'MEDIUM': 'Moderate AML risk. Transaction logged and account placed under enhanced monitoring for 30 days.',
        'LOW': 'Transaction within normal AML parameters. Cleared for processing.'
    }

    steps = {
        'CRITICAL': ['All linked accounts immediately frozen', 'Suspicious Transaction Report filed with FIU-IND', 'FATF jurisdiction alert raised', 'Case escalated to compliance and legal', 'Law enforcement notified if threshold exceeded'],
        'HIGH': ['Transaction held for 48-hour compliance review', 'Enhanced KYC documents requested from customer', 'Account flagged for enhanced ongoing monitoring', 'Relationship manager alerted'],
        'MEDIUM': ['Transaction approved with enhanced logging', 'Account placed on 30-day watchlist', 'Next transaction from this account auto-reviewed'],
        'LOW': ['Transaction cleared — no AML concerns', 'Standard monitoring continues', 'Behavioral baseline updated']
    }

    return {
        'score': score,
        'factors': {
            'transactionAmount': {'score': fAmt, 'detail': f"₹{amt:,.2f} — near ₹1L reporting threshold (smurfing pattern)" if struct else f"₹{amt:,.2f}"},
            'transactionVolume': {'score': fTxc, 'detail': f"{txc} transactions in 24h — {'layering velocity detected' if fTxc >= 60 else 'normal volume'}"},
            'accountAge': {'score': fAge, 'detail': f"{age} months old — {'new account, high bust-out risk' if fAge >= 70 else 'established account'}"},
            'jurisdictionRisk': {'score': fCty, 'detail': f"{country} — {'FATF high-risk jurisdiction' if fCty >= 70 else 'standard jurisdiction'}"},
            'crossBorderFlag': {'score': fCross, 'detail': 'Cross-border transfer — layering risk elevated' if cross else 'Domestic transfer'},
            'shellCompanyRisk': {'score': fShell, 'detail': 'Beneficiary identified as shell company — integration stage risk' if shell else 'Legitimate beneficiary entity'},
            'structuringPattern': {'score': fStruct, 'detail': 'Amount structured below ₹1L reporting threshold — smurfing indicator' if struct else 'No structuring pattern detected'}
        },
        'verdict': {'level': level, 'action': action, 'message': messages[level], 'steps': steps[level]}
    }


# ── Unauthorized Transaction Analyzer ───────────────────────

def analyzeUT(p):
    amt = float(p.get('amount', 0) or 0)
    hour = int(p.get('hour', 12) or 12)
    age = int(p.get('accountAgeMonths', 24) or 24)
    country = p.get('country', 'IN') or 'IN'
    newDev = to_bool(p.get('newDevice', False))
    newBen = to_bool(p.get('newBeneficiary', False))
    otp = to_bool(p.get('multipleOtpFail', False))
    cred = to_bool(p.get('credentialChange', False))
    geo = to_bool(p.get('geoMismatch', False))

    fAmt = amountScore(amt, 5000, 100000)
    fHr = hourScore(hour)
    fAge = 30 if age <= 3 else 5
    fCty = countryScore(country)
    fDev = 80 if newDev else 5
    fBen = 75 if newBen else 5
    fOtp = 90 if otp else 5
    fCred = 85 if cred else 5
    fGeo = 80 if geo else 5

    fCred = 85 if cred else 5
    fGeo = 80 if geo else 5

    if MODELS['UT']:
        df = pd.DataFrame([{
            'amount': amt, 'hour': hour, 'accountAgeMonths': age,
            'newDevice': 1 if newDev else 0, 'newBeneficiary': 1 if newBen else 0,
            'multipleOtpFail': 1 if otp else 0, 'credentialChange': 1 if cred else 0,
            'geoMismatch': 1 if geo else 0
        }])
        score = min(100, round(MODELS['UT'].predict_proba(df)[0][1] * 100))
    else:
        score = min(100, round(
            fAmt * 0.12 + fHr * 0.10 + fAge * 0.05 + fCty * 0.05 +
            fDev * 0.18 + fBen * 0.15 + fOtp * 0.15 + fCred * 0.10 + fGeo * 0.10
        ))

    level = 'CRITICAL' if score >= 75 else 'HIGH' if score >= 50 else 'MEDIUM' if score >= 25 else 'LOW'
    action = 'BLOCK & FREEZE ACCOUNT' if score >= 75 else 'BLOCK & VERIFY IDENTITY' if score >= 50 else 'STEP-UP AUTH' if score >= 25 else 'APPROVE'

    messages = {
        'CRITICAL': 'High-confidence account takeover detected. SIM swap indicators present: new device, credential change, OTP bypass, and immediate large transfer to unknown beneficiary. Account frozen.',
        'HIGH': 'Account takeover pattern detected — new device plus immediate transfer to unknown beneficiary. Transaction blocked pending identity verification.',
        'MEDIUM': 'Suspicious access pattern. Step-up authentication required before processing.',
        'LOW': 'Transaction consistent with normal account behavior. Approved.'
    }

    steps = {
        'CRITICAL': ['Transaction immediately blocked', 'Account frozen — all channels suspended', 'Customer contacted via registered email (not SMS — SIM may be compromised)', 'SIM swap investigation initiated with telecom provider', 'New device registration revoked', 'Incident report filed'],
        'HIGH': ['Transaction held — identity verification required', 'Video KYC or branch visit required to unfreeze', 'New beneficiary registration rejected', 'Account activity monitored in real-time'],
        'MEDIUM': ['Step-up OTP sent to registered mobile', 'Transaction delayed 5 minutes pending verification', 'Beneficiary added to watchlist'],
        'LOW': ['Transaction approved', 'New behavioral data point recorded', 'No further action required']
    }

    return {
        'score': score,
        'factors': {
            'transactionAmount': {'score': fAmt, 'detail': f"₹{amt:,.2f} — {'large amount to new beneficiary is high risk' if fAmt >= 60 else 'amount within normal range'}"},
            'offHoursAccess': {'score': fHr, 'detail': f"Login at {hour}:00 — {'peak account-takeover window' if fHr >= 70 else 'normal hours'}"},
            'newDeviceDetected': {'score': fDev, 'detail': 'Unregistered device — never used with this account' if newDev else 'Known registered device'},
            'newBeneficiary': {'score': fBen, 'detail': 'Transfer to first-time beneficiary within minutes of login' if newBen else 'Transfer to known beneficiary'},
            'otpFailureChain': {'score': fOtp, 'detail': 'Multiple OTP failures before eventual success — brute-force indicator' if otp else 'Authentication completed normally'},
            'credentialChange': {'score': fCred, 'detail': 'Password/PIN changed 30 minutes before this transaction' if cred else 'No recent credential changes'},
            'geographicMismatch': {'score': fGeo, 'detail': 'Login IP geolocation does not match account registration country' if geo else 'IP consistent with account location'}
        },
        'verdict': {'level': level, 'action': action, 'message': messages[level], 'steps': steps[level]}
    }


# ── Fake Transaction Analyzer ────────────────────────────────

def analyzeFT(p):
    amt = float(p.get('amount', 0) or 0)
    age = int(p.get('accountAgeMonths', 12) or 12)
    mr = float(p.get('merchantRisk', 0) or 0)
    cb = int(p.get('chargebackHistory', 0) or 0)
    synth = to_bool(p.get('syntheticId', False))
    ghost = to_bool(p.get('ghostMerchant', False))
    bust = to_bool(p.get('rapidCreditUtilisation', False))
    infl = to_bool(p.get('invoiceInflation', False))

    fAmt = amountScore(amt, 500, 50000)
    fAge = 85 if age <= 3 else 40 if age <= 12 else 10
    fMr = round(mr * 100)
    fCb = min(100, cb * 15)
    fSynth = 88 if synth else 5
    fGhost = 85 if ghost else 5
    fBust = 90 if bust else 5
    fInfl = 75 if infl else 5

    fBust = 90 if bust else 5
    fInfl = 75 if infl else 5

    if MODELS['FT']:
        df = pd.DataFrame([{
            'amount': amt, 'accountAgeMonths': age, 'merchantRisk': mr,
            'chargebackHistory': cb, 'syntheticId': 1 if synth else 0,
            'ghostMerchant': 1 if ghost else 0,
            'rapidCreditUtilisation': 1 if bust else 0, 'invoiceInflation': 1 if infl else 0
        }])
        score = min(100, round(MODELS['FT'].predict_proba(df)[0][1] * 100))
    else:
        score = min(100, round(
            fAmt * 0.10 + fAge * 0.15 + fMr * 0.15 + fCb * 0.15 +
            fSynth * 0.15 + fGhost * 0.15 + fBust * 0.10 + fInfl * 0.05
        ))

    level = 'CRITICAL' if score >= 75 else 'HIGH' if score >= 50 else 'MEDIUM' if score >= 25 else 'LOW'
    action = 'REJECT & INVESTIGATE' if score >= 75 else 'REJECT & REVIEW' if score >= 50 else 'FLAG FOR REVIEW' if score >= 25 else 'APPROVE'

    messages = {
        'CRITICAL': 'Synthetic identity bust-out fraud confirmed. Ghost merchant, fabricated behavioral profile, and rapid credit utilisation detected. Transaction permanently rejected — Economic Offences Wing referral initiated.',
        'HIGH': 'Strong synthetic identity indicators. Account exhibits statistically impossible behavioral patterns. Transaction rejected pending full investigation.',
        'MEDIUM': 'Elevated fake transaction risk — chargeback history and merchant risk signals present. Manual review required.',
        'LOW': 'Transaction appears legitimate. No synthetic identity or fake merchant signals detected.'
    }

    steps = {
        'CRITICAL': ['Transaction permanently rejected', 'All linked accounts suspended', 'Merchant ID blacklisted across network', 'Synthetic identity report filed', 'EOW referral initiated', 'Credit bureau notified of fabricated identity'],
        'HIGH': ['Transaction rejected', 'Account suspended pending KYC re-verification', 'Merchant flagged for investigation', 'Chargeback history reviewed by risk team'],
        'MEDIUM': ['Transaction held for 24-hour manual review', 'Additional merchant verification requested', 'Customer asked to provide transaction documentation'],
        'LOW': ['Transaction approved and settled', 'Merchant and account profiles updated', 'No further action required']
    }

    return {
        'score': score,
        'factors': {
            'transactionAmount': {'score': fAmt, 'detail': f"₹{amt:,.2f} — {'inflated amount relative to account profile' if fAmt >= 60 else 'consistent with account spending'}"},
            'accountAge': {'score': fAge, 'detail': f"{age} months old — {'new account with impossible behavioral history' if fAge >= 70 else 'established account'}"},
            'merchantRiskScore': {'score': fMr, 'detail': f"Merchant risk: {round(mr * 100)}% — {'ghost/non-existent merchant' if fMr >= 70 else 'elevated merchant risk' if fMr >= 40 else 'legitimate merchant'}"},
            'chargebackHistory': {'score': fCb, 'detail': f"{cb} previous chargebacks — {'serial chargeback fraud pattern' if fCb >= 60 else 'some chargeback history' if cb > 0 else 'clean chargeback record'}"},
            'syntheticIdentity': {'score': fSynth, 'detail': 'Identity shows hallmarks of synthetic fabrication — credit-building pattern detected' if synth else 'Identity documents appear genuine'},
            'ghostMerchantFlag': {'score': fGhost, 'detail': 'Merchant has no physical presence, no web footprint, zero transaction history before this week' if ghost else 'Merchant appears legitimate'},
            'bustOutPattern': {'score': fBust, 'detail': 'Credit utilisation 0%→95% in <48 hours across multiple accounts — bust-out confirmed' if bust else 'Normal credit utilisation pattern'},
            'invoiceInflation': {'score': fInfl, 'detail': 'Invoice amount significantly above market rate for stated goods/services' if infl else 'Invoice amount consistent with market rates'}
        },
        'verdict': {'level': level, 'action': action, 'message': messages[level], 'steps': steps[level]}
    }


# ── Identity Theft Analyzer ────────────────────────────────

def analyzeIT(p):
    amt = float(p.get('amount', 0) or 0)
    pwd = to_bool(p.get('frequentPwdChange', False))
    doc = to_bool(p.get('fakeDocuments', False))
    cred = to_bool(p.get('creditPull', False))

    fAmt = amountScore(amt, 2000, 20000)
    
    if MODELS['IT']:
        df = pd.DataFrame([{
            'amount': amt, 'frequentPwdChange': 1 if pwd else 0,
            'fakeDocuments': 1 if doc else 0, 'creditPull': 1 if cred else 0
        }])
        score = min(100, round(MODELS['IT'].predict_proba(df)[0][1] * 100))
    else:
        score = 5 + round(fAmt * 0.1)
        if pwd: score += 30
        if doc: score += 45
        if cred: score += 20

    level = 'CRITICAL' if score >= 75 else 'HIGH' if score >= 50 else 'MEDIUM' if score >= 25 else 'LOW'
    action = 'LOCK IDENTITY' if score >= 75 else 'STEP-UP AUTH' if score >= 50 else 'FLAG' if score >= 25 else 'APPROVE'

    messages = {
        'CRITICAL': 'Severe Identity Theft signals present. Fraudulent verification documents combined with sudden credit inquiries. Pre-emptive identity lock initiated.',
        'HIGH': 'Elevated suspicion of Identity Takeover. Requires in-person KYC re-verification.',
        'MEDIUM': 'Unusual password reset looping or unexpected credit pulls. Flagged for review.',
        'LOW': 'Identity signals match normal behavior. Approved.'
    }

    steps = {
        'CRITICAL': ['Lock Account', 'Require In-Person KYC', 'Alert Credit Bureaus'],
        'HIGH': ['Suspend Credit Features', 'Push Video KYC Requirement'],
        'MEDIUM': ['Flag for Analyst Review', 'Monitor Social Triggers'],
        'LOW': ['Standard Monitoring', 'No Action']
    }

    return {
        'score': min(100, score),
        'factors': {
            'passwordChanges': {'score': 30 if pwd else 0, 'detail': 'Frequent password resets' if pwd else 'Normal'},
            'documentVerification': {'score': 45 if doc else 0, 'detail': 'Fake ID documents detected' if doc else 'Genuine'},
            'creditPulls': {'score': 20 if cred else 0, 'detail': 'Multiple recent credit inquiries' if cred else 'Normal'},
            'transactionAmount': {'score': fAmt, 'detail': f"₹{amt:,.2f} risk score"}
        },
        'verdict': {'level': level, 'action': action, 'message': messages[level], 'steps': steps[level]}
    }

# ── Transaction Simulator ────────────────────────────────────


class Simulator:
    def __init__(self):
        database.init_db()
        loaded_stats = database.get_stats()
        if loaded_stats:
            self.stats = loaded_stats
        else:
            self.stats = {
                'total': 0, 'fraud': 0, 'suspect': 0, 'clean': 0,
                'ccFraud': 0, 'mlFraud': 0, 'utFraud': 0, 'ftFraud': 0, 'itFraud': 0,
                'blockedAmount': 0, 'accuracy': 97.3, 'fraudRate': 0.0
            }

        # Make sure itFraud exists inside stats if migrating from older version
        if 'itFraud' not in self.stats:
            self.stats['itFraud'] = 0

        self.transactions = database.get_recent_transactions(limit=500)
        self.flRound = self.stats.get('round', 47)
        self.accuracy = self.stats.get('accuracy', 97.3)
        self.epsilon = self.stats.get('epsilon', 0.9)

    def generate(self, forcedType=None):
        isFraud = True if forcedType else random.random() < 0.08
        isSuspect = False if isFraud else random.random() < 0.12
        fraudType = forcedType or (pick(FRAUD_TYPES) if isFraud else None)

        bankSrc = pick(BANKS)
        bankDst = pick(BANKS)
        while bankDst == bankSrc:
            bankDst = pick(BANKS)

        country = pick(['RU', 'NG', 'CN', 'AE', 'US']
                       ) if isFraud else pick(COUNTRIES)
        hour = randInt(0, 5) if isFraud else randInt(8, 22)
        amount = randInt(50000, 500000) if isFraud else randInt(500, 25000)

        score = randInt(75, 98) if isFraud else (
            randInt(45, 74) if isSuspect else randInt(5, 35))
        status = 'fraud' if isFraud else 'suspect' if isSuspect else 'clean'
        latency = randInt(5, 18)

        labels = {
            'CC': 'Credit Card Fraud',
            'ML': 'Money Laundering',
            'UT': 'Unauthorized Transaction',
            'FT': 'Fake Transaction',
            'IT': 'Identity Theft'}

        tx = {
            'id': uid(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'bankSrc': bankSrc,
            'bankDst': bankDst,
            'amount': f"{amount:.2f}",
            'hour': hour,
            'country': country,
            'status': status,
            'fraudType': fraudType,
            'fraudLabel': labels.get(fraudType) if fraudType else None,
            'score': score,
            'latency': latency,
            'device': pick(DEVICES)
        }

        # Update stats
        self.stats['total'] += 1
        if isFraud:
            self.stats['fraud'] += 1
            self.stats['blockedAmount'] += amount
            if fraudType == 'CC':
                self.stats['ccFraud'] += 1
            if fraudType == 'ML':
                self.stats['mlFraud'] += 1
            if fraudType == 'UT':
                self.stats['utFraud'] += 1
            if fraudType == 'FT':
                self.stats['ftFraud'] += 1
            if fraudType == 'IT':
                self.stats['itFraud'] += 1
        if isSuspect:
            self.stats['suspect'] += 1
        if not isFraud and not isSuspect:
            self.stats['clean'] += 1

        self.stats['fraudRate'] = float(
            f"{(self.stats['fraud'] / self.stats['total']) * 100:.2f}") if self.stats['total'] > 0 else 0.0

        self.transactions.insert(0, tx)
        if len(self.transactions) > 500:
            self.transactions.pop()

        # Persistence
        database.save_transaction(tx)
        self.stats['accuracy'] = self.accuracy
        self.stats['round'] = self.flRound
        self.stats['epsilon'] = self.epsilon
        database.save_stats(self.stats)

        return tx

    def flTick(self):
        self.flRound += 1
        self.epsilon = round(self.epsilon + rand(0.04, 0.09), 3)
        self.accuracy = round(min(99.1, self.accuracy + rand(-0.05, 0.15)), 1)
        self.stats['accuracy'] = self.accuracy
        self.stats['round'] = self.flRound
        self.stats['epsilon'] = self.epsilon
        database.save_stats(self.stats)

    def getStats(self):
        stats_copy = dict(self.stats)
        stats_copy.update({
            'round': self.flRound,
            'epsilon': self.epsilon,
            'accuracy': self.accuracy
        })
        return stats_copy

    def getBanks(self):
        return [
            {
                'id': i,
                'name': name,
                'status': 'active',
                'accuracy': round(rand(94, 99), 1),
                'txCount': randInt(1000, 50000),
                'flRound': self.flRound
            }
            for i, name in enumerate(BANKS)
        ]
