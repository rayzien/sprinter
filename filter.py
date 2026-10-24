import re

KYC_PATTERNS = [
    r'паспорт', r'вериф', r'kyc', r'паспортные', r'passport', r'id\s*card',
    r'селфи', r'selfie', r'документ', r'личность', r'госуслуги', r'тинькофф'
]

PHONE_SMS_PATTERNS = [
    r'номер телефона', r'смс', r'sms', r'код из смс', r'подтвердить номер',
    r'привязать телефон', r'звонок', r'привязать номер', r'phone number', r'otp'
]

FINANCIAL_PATTERNS = [
    r'депозит', r'deposit', r'вложить', r'вложения', r'пополнить баланс',
    r'пополнение', r'купить', r'оплата', r'инвестиц', r'казино', r'casino', r'ставки'
]

LONG_GRIND_PATTERNS = [
    r'\bдней\b', r'\bнеделю\b', r'\bуровень\b', r'\bпрокачать\b', r'\blvl\b',
    r'\blevel\b', r'каждый день заходить', r'активность в течение'
]

SIGNUP_PATTERNS = [
    r'регистрация', r'рега', r'email', r'почта', r'почт', r'подтвердить почту',
    r'sign\s*up', r'signup', r'register', r'аккаунт', r'письмо', r'активация',
    r'скачать', r'приложение', r'app', r'android', r'apk', r'установка', r'телефон', r'mobile'
]

NEGATION_REGEX = re.compile(r'(?:no|without|not|без|не\s+нужно|не\s+требуется)\s+[^\.\,\;]{0,25}$', re.I)

def parse_price(text):
    if not text:
        return 0.0
    usd = re.search(r'([\d\.,]+)\s*(\$|usd)', text, re.I) or re.search(r'(\$)\s*([\d\.,]+)', text, re.I)
    if usd:
        val = usd.group(2) if usd.group(1) == '$' else usd.group(1)
        return float(val.replace(',', '.'))
    rub = re.search(r'([\d\.,]+)\s*(руб|₽|rub)', text, re.I)
    if rub:
        return float(rub.group(1).replace(',', '.')) / 95.0
    num = re.search(r'[\d\.,]+', text)
    if num:
        return float(num.group(0).replace(',', '.'))
    return 0.0

def evaluate_task(title, desc="", price=0.0):
    text = (title + " " + desc).lower()

    # 1. Reject KYC
    for pat in KYC_PATTERNS:
        match = re.search(pat, text, re.I)
        if match:
            prefix = text[max(0, match.start() - 25):match.start()]
            if not NEGATION_REGEX.search(prefix):
                return {
                    "valid": False,
                    "score": 0,
                    "reason": f"Requires KYC / Identity ({match.group(0)})",
                    "category": "Rejected"
                }

    # 2. Reject Phone Number / SMS
    for pat in PHONE_SMS_PATTERNS:
        match = re.search(pat, text, re.I)
        if match:
            prefix = text[max(0, match.start() - 25):match.start()]
            if not NEGATION_REGEX.search(prefix):
                return {
                    "valid": False,
                    "score": 0,
                    "reason": f"Requires Phone / SMS verification ({match.group(0)})",
                    "category": "Rejected"
                }

    # 3. Reject Deposits / Financial
    for pat in FINANCIAL_PATTERNS:
        match = re.search(pat, text, re.I)
        if match:
            prefix = text[max(0, match.start() - 25):match.start()]
            if not NEGATION_REGEX.search(prefix):
                return {
                    "valid": False,
                    "score": 0,
                    "reason": f"Requires deposit / purchase ({match.group(0)})",
                    "category": "Rejected"
                }

    # 4. Reject multi-day grind
    for pat in LONG_GRIND_PATTERNS:
        if re.search(pat, text, re.I):
            return {
                "valid": False,
                "score": 0,
                "reason": "Exceeds 2-3 minute timeframe (multi-day grind)",
                "category": "Rejected"
            }

    # 5. Must match Email Signup / Phone task
    has_signup = False
    for pat in SIGNUP_PATTERNS:
        if re.search(pat, text, re.I):
            has_signup = True
            break

    if not has_signup:
        return {
            "valid": False,
            "score": 10,
            "reason": "Not an email signup or mobile task",
            "category": "Unmatched"
        }

    # Calculate score based on speed and payout
    score = 65
    if any(k in text for k in ['простая', 'быстро', 'клик', 'почту', 'email', 'письмо']):
        score += 20
    if price >= 0.05:
        score += 15
    elif price >= 0.02:
        score += 5
    elif price < 0.01:
        score -= 10

    score = max(10, min(100, score))
    category = "Mobile App" if any(k in text for k in ['android', 'apk', 'приложение', 'app']) else "Email Signup"

    return {
        "valid": True,
        "score": score,
        "reason": "Fast 2-3 min email/mobile signup without KYC/SMS",
        "category": category
    }
