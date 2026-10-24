import re

KYC_PATTERNS = [
    r'паспорт', r'вериф', r'kyc', r'паспортные', r'passport', r'id\s*card',
    r'селфи', r'selfie', r'документ', r'личность', r'госуслуги', r'тинькофф'
]

PHONE_SMS_PATTERNS = [
    r'номер телефона', r'смс', r'sms', r'код из смс', r'подтвердить номер',
    r'привязать телефон', r'звонок', r'привязать номер', r'phone number', r'otp',
    r'мобильный номер', r'смс-код', r'привязка номера'
]

FINANCIAL_PATTERNS = [
    r'депозит', r'deposit', r'вложить', r'вложения', r'пополнить баланс',
    r'пополнение', r'купить', r'оплата', r'инвестиц', r'казино', r'casino', r'ставки'
]

LONG_GRIND_PATTERNS = [
    r'\bдней\b', r'\bнеделю\b', r'\bуровень\b', r'\bпрокачать\b', r'\blvl\b',
    r'\blevel\b', r'каждый день заходить', r'активность в течение', r'10\s*минут',
    r'15\s*минут', r'20\s*минут', r'30\s*минут', r'1\s*час'
]

SIGNUP_PATTERNS = [
    r'регистрация', r'рега', r'email', r'почта', r'почт', r'подтвердить почту',
    r'sign\s*up', r'signup', r'register', r'аккаунт', r'письмо', r'активация',
    r'скачать', r'приложение', r'app', r'android', r'apk', r'установка', r'телефон', r'mobile'
]

NEGATION_REGEX = re.compile(r'(?:no|without|not|без|не\s+нужно|не\s+требуется|не\s+надо)\s+[^\.\,\;]{0,25}$', re.I)

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

def estimate_time_minutes(title, desc=""):
    text = (title + " " + desc).lower()
    # Fast clicks / quick email confirm: 1.0 - 1.5 min
    if any(k in text for k in ['клик', 'переход', 'быстрый', 'секунд', '1 мин', 'быстро']):
        return 1.5
    # Standard registration only: 2.0 min
    if any(k in text for k in ['только регистрация', 'без активности', 'простая рега', 'простая регистрация']):
        return 2.0
    # App install: 3.0 - 3.5 min
    if any(k in text for k in ['скачать', 'установить', 'apk', 'приложение', 'app']):
        return 3.5
    # Email confirm / multi-field: 2.5 min
    if any(k in text for k in ['подтвердить почту', 'активация', 'email']):
        return 2.5
    return 3.0

def evaluate_task(title, desc="", price=0.0):
    text = (title + " " + desc).lower()

    # 1. Reject KYC / Face / Passport
    for pat in KYC_PATTERNS:
        match = re.search(pat, text, re.I)
        if match:
            prefix = text[max(0, match.start() - 25):match.start()]
            if not NEGATION_REGEX.search(prefix):
                return {
                    "valid": False,
                    "score": 0,
                    "reason": f"Requires KYC / Identity ({match.group(0)})",
                    "category": "Rejected",
                    "est_minutes": 99.0
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
                    "category": "Rejected",
                    "est_minutes": 99.0
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
                    "category": "Rejected",
                    "est_minutes": 99.0
                }

    # 4. Reject multi-day grind or > 5 min tasks
    for pat in LONG_GRIND_PATTERNS:
        if re.search(pat, text, re.I):
            return {
                "valid": False,
                "score": 0,
                "reason": "Exceeds 5-minute timeframe limit",
                "category": "Rejected",
                "est_minutes": 15.0
            }

    # 5. Must match Email Signup or Android/Phone task
    has_signup = False
    for pat in SIGNUP_PATTERNS:
        if re.search(pat, text, re.I):
            has_signup = True
            break

    if not has_signup:
        return {
            "valid": False,
            "score": 10,
            "reason": "Not an email signup or Android mobile task",
            "category": "Unmatched",
            "est_minutes": 10.0
        }

    est_min = estimate_time_minutes(title, desc)
    if est_min > 5.0:
        return {
            "valid": False,
            "score": 0,
            "reason": "Estimated time exceeds 5 minutes",
            "category": "Rejected",
            "est_minutes": est_min
        }

    # Calculate score based on speed, payout, and ease
    score = 70
    if est_min <= 2.0:
        score += 20
    elif est_min <= 3.0:
        score += 10

    if price >= 0.05:
        score += 15
    elif price >= 0.02:
        score += 5
    elif price < 0.01:
        score -= 5

    score = max(10, min(100, score))
    category = "Android App" if any(k in text for k in ['android', 'apk', 'приложение', 'app']) else "Email Signup"

    return {
        "valid": True,
        "score": score,
        "reason": f"Fast {est_min:.1f} min email/mobile signup without KYC/SMS",
        "category": category,
        "est_minutes": est_min
    }

def translate_ru_to_en(text):
    """Common SEOSprint dictionary translator for instant rapid comprehension"""
    replacements = [
        ("Только регистрация", "Registration Only"),
        ("без активности", "No activity required"),
        ("Быстрая регистрация", "Fast Registration"),
        ("Подтвердить почту", "Confirm email address"),
        ("Подтверждение по почте", "Email confirmation link"),
        ("В отчёт", "What to submit in report"),
        ("В отчет", "What to submit in report"),
        ("Логин", "Username/Login"),
        ("Скриншот", "Screenshot"),
        ("Ссылка на профиль", "Profile Link"),
        ("Никнейм", "Nickname"),
        ("Почта", "Email"),
        ("Установить приложение", "Install Mobile App"),
        ("Скачать", "Download APK/App"),
        ("Открыть", "Open application"),
        ("Начать выполнение", "Start execution"),
        ("Отправить отчёт", "Submit report"),
        ("Простая", "Simple"),
        ("Быстро", "Fast"),
        ("Оплата сразу", "Immediate payout")
    ]
    res = text
    for ru, en in replacements:
        res = re.sub(re.escape(ru), en, res, flags=re.I)
    return res
