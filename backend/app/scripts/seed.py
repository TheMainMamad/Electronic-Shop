"""Idempotent demo data for dev/staging (Phase 11).

Populates the Persian category tree, ~25 products, an admin + a customer
account, a handful of orders/payments in different states, a few wallet
ledger entries and one closed support ticket. Every block checks for its own
rows first (by slug/sku/email/note/reference or, for the order bundle, by
"does this customer already have any orders") before writing anything, so
re-running this script is always a no-op on the second pass — see
docs/architecture.md's concurrency-safe upsert pattern used throughout the
service layer (e.g. WalletService.get_or_create's ON CONFLICT DO NOTHING).

Run with:
    python -m app.scripts.seed
"""

import asyncio
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db import model_registry  # noqa: F401 - registers all models on Base.metadata
from app.db.session import AsyncSessionFactory
from app.modules.auth.repository import UserRepository
from app.modules.cart.service import CartService
from app.modules.catalog.models import Category, Product
from app.modules.catalog.repository import CategoryRepository, ProductRepository
from app.modules.catalog.schemas import CategoryCreate, ProductCreate
from app.modules.catalog.service import CategoryService, ProductService
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import ShippingAddress
from app.modules.orders.service import OrderService
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.tickets.models import Ticket, TicketMessage, TicketPriority, TicketStatus
from app.modules.tickets.service import TicketService
from app.modules.users.models import User, UserRole
from app.modules.wallet.models import WalletTransaction, WalletTransactionType
from app.modules.wallet.service import WalletService
from app.security.password import hash_password

logger = structlog.get_logger()

ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "AdminDemo@1404")
CUSTOMER_EMAIL = os.environ.get("SEED_CUSTOMER_EMAIL", "customer@example.com")
CUSTOMER_PASSWORD = os.environ.get("SEED_CUSTOMER_PASSWORD", "CustomerDemo@1404")

CATEGORY_TREE: list[dict[str, Any]] = [
    {
        "name": "موبایل و تبلت",
        "slug": "mobile-tablet",
        "children": [
            {"name": "گوشی موبایل", "slug": "mobile-phones"},
            {"name": "تبلت", "slug": "tablets"},
            {"name": "لوازم جانبی موبایل", "slug": "mobile-accessories"},
        ],
    },
    {
        "name": "لپ‌تاپ و کامپیوتر",
        "slug": "laptop-computer",
        "children": [
            {"name": "لپ‌تاپ", "slug": "laptops"},
            {"name": "قطعات کامپیوتر", "slug": "computer-parts"},
            {"name": "لوازم جانبی کامپیوتر", "slug": "computer-accessories"},
        ],
    },
    {
        "name": "صوتی و تصویری",
        "slug": "audio-video",
        "children": [
            {"name": "هدفون و هندزفری", "slug": "headphones"},
            {"name": "اسپیکر", "slug": "speakers"},
            {"name": "تلویزیون", "slug": "televisions"},
        ],
    },
    {
        "name": "لوازم خانگی",
        "slug": "home-appliances",
        "children": [
            {"name": "لوازم خانگی برقی کوچک", "slug": "small-appliances"},
            {"name": "یخچال و فریزر", "slug": "refrigerators"},
        ],
    },
    {
        "name": "گیمینگ",
        "slug": "gaming",
        "children": [
            {"name": "کنسول بازی", "slug": "game-consoles"},
            {"name": "لوازم جانبی گیمینگ", "slug": "gaming-accessories"},
        ],
    },
]

# Real product photography isn't ours to license, so each category maps to a
# free-to-use Unsplash photo (Unsplash License: free for commercial and
# noncommercial use, no permission needed) rather than an illustrated icon.
CATEGORY_PHOTO_IDS: dict[str, str] = {
    "mobile-phones": "1544237515-4480d7d7ff8c",
    "tablets": "1693257260074-77098c29c6dc",
    "mobile-accessories": "1499033300314-43c811cff6d5",
    "laptops": "1572666341285-c8cb9790ca50",
    "computer-parts": "1733741020205-1ed0208314b6",
    "computer-accessories": "1662758392656-0e5d4b0f53fb",
    "headphones": "1505740420928-5e560c06d30e",
    "speakers": "1542483381-41a479b1fb88",
    "televisions": "1631679893114-7957e44879db",
    "small-appliances": "1693875161720-b0c2401c1874",
    "refrigerators": "1588854337048-44569c79c614",
    "game-consoles": "1653757398818-5016ba6d2594",
    "gaming-accessories": "1616296425622-4560a2ad83de",
}


def category_placeholder_image(category_slug: str) -> str:
    photo_id = CATEGORY_PHOTO_IDS[category_slug]
    return f"https://images.unsplash.com/photo-{photo_id}?fm=jpg&q=80&w=800&auto=format&fit=crop"



PRODUCTS: list[dict[str, Any]] = [
    {
        "sku": "SGX-A54-128",
        "slug": "samsung-galaxy-a54",
        "name": "گوشی موبایل سامسونگ گلکسی A54",
        "short_description": "گوشی میان‌رده با نمایشگر Super AMOLED و دوربین ۵۰ مگاپیکسلی",
        "description": (
            "سامسونگ گلکسی A54 با نمایشگر ۶.۴ اینچی Super AMOLED با نرخ به‌روزرسانی ۱۲۰ هرتز، "
            "دوربین اصلی ۵۰ مگاپیکسل با تثبیت‌کننده نوری تصویر و باتری ۵۰۰۰ میلی‌آمپرساعتی، "
            "انتخابی مناسب برای استفاده روزمره و عکاسی است."
        ),
        "price": "24500000",
        "discount_price": "22900000",
        "brand": "سامسونگ",
        "category_slug": "mobile-phones",
        "specifications": {
            "حافظه داخلی": "128 گیگابایت",
            "رم": "8 گیگابایت",
            "نمایشگر": "6.4 اینچ Super AMOLED",
            "دوربین اصلی": "50 مگاپیکسل",
            "باتری": "5000 میلی‌آمپرساعت",
        },
        "initial_stock": 40,
        "is_featured": True,
        "is_popular": True,
    },
    {
        "sku": "XIA-R12-256",
        "slug": "xiaomi-redmi-note-12",
        "name": "گوشی موبایل شیائومی ردمی نوت 12",
        "short_description": "گوشی مقرون‌به‌صرفه با شارژ سریع ۳۳ واتی و نمایشگر AMOLED",
        "description": (
            "ردمی نوت ۱۲ با پردازنده اسنپدراگون، نمایشگر AMOLED فول اچ‌دی و شارژر سریع ۳۳ وات "
            "همراه جعبه، گزینه‌ای اقتصادی برای کاربران عمومی است."
        ),
        "price": "12300000",
        "brand": "شیائومی",
        "category_slug": "mobile-phones",
        "specifications": {
            "حافظه داخلی": "256 گیگابایت",
            "رم": "8 گیگابایت",
            "نمایشگر": "6.67 اینچ AMOLED",
            "شارژ سریع": "33 وات",
        },
        "initial_stock": 55,
        "is_popular": True,
    },
    {
        "sku": "APL-IP13-128",
        "slug": "apple-iphone-13",
        "name": "گوشی موبایل اپل آیفون 13",
        "short_description": "آیفون ۱۳ با تراشه A15 Bionic و دوربین دوگانه پیشرفته",
        "description": (
            "آیفون ۱۳ با تراشه قدرتمند A15 Bionic، دوربین دوگانه ۱۲ مگاپیکسلی و پشتیبانی از "
            "ضبط ویدیوی سینمایی، همچنان یکی از پرفروش‌ترین آیفون‌های بازار ایران است."
        ),
        "price": "38900000",
        "discount_price": "36500000",
        "brand": "اپل",
        "category_slug": "mobile-phones",
        "specifications": {
            "حافظه داخلی": "128 گیگابایت",
            "تراشه": "Apple A15 Bionic",
            "نمایشگر": "6.1 اینچ Super Retina XDR",
        },
        "initial_stock": 20,
        "is_featured": True,
    },
    {
        "sku": "SGX-S23-256",
        "slug": "samsung-galaxy-s23",
        "name": "گوشی موبایل سامسونگ گلکسی S23",
        "short_description": "پرچمدار سامسونگ با دوربین ۵۰ مگاپیکسل و پردازنده اسنپدراگون",
        "description": (
            "گلکسی S23 با بدنه فشرده، پردازنده Snapdragon 8 Gen 2 برای گلکسی و دوربین اصلی "
            "۵۰ مگاپیکسلی، تجربه‌ای پرچمدار در اندازه‌ای جمع‌وجور ارائه می‌دهد."
        ),
        "price": "42000000",
        "brand": "سامسونگ",
        "category_slug": "mobile-phones",
        "specifications": {
            "حافظه داخلی": "256 گیگابایت",
            "رم": "8 گیگابایت",
            "پردازنده": "Snapdragon 8 Gen 2",
        },
        "initial_stock": 18,
    },
    {
        "sku": "APL-IPADA9",
        "slug": "apple-ipad-9th-gen",
        "name": "تبلت اپل آیپد نسل نهم",
        "short_description": "تبلت ۱۰.۲ اینچی اپل با تراشه A13 Bionic، مناسب کار و آموزش",
        "description": (
            "آیپد نسل نهم با نمایشگر ۱۰.۲ اینچی Retina و تراشه A13 Bionic، برای مطالعه، "
            "یادداشت‌برداری با اپل پنسل نسل اول و استفاده‌های روزمره مناسب است."
        ),
        "price": "21500000",
        "brand": "اپل",
        "category_slug": "tablets",
        "specifications": {
            "حافظه داخلی": "64 گیگابایت",
            "نمایشگر": "10.2 اینچ Retina",
            "پشتیبانی قلم": "Apple Pencil نسل اول",
        },
        "initial_stock": 25,
        "is_popular": True,
    },
    {
        "sku": "SGX-TABS6L",
        "slug": "samsung-galaxy-tab-s6-lite",
        "name": "تبلت سامسونگ گلکسی تب S6 Lite",
        "short_description": "تبلت همراه با قلم S Pen، مناسب یادداشت‌برداری و طراحی",
        "description": (
            "گلکسی تب S6 Lite به همراه قلم S Pen عرضه می‌شود و برای یادداشت‌برداری، طراحی و "
            "سرگرمی روزمره گزینه‌ای اقتصادی در برابر پرچمدارهای اپل است."
        ),
        "price": "15800000",
        "brand": "سامسونگ",
        "category_slug": "tablets",
        "specifications": {"حافظه داخلی": "128 گیگابایت", "قلم همراه": "S Pen"},
        "initial_stock": 30,
    },
    {
        "sku": "ANK-CHG20W",
        "slug": "anker-charger-20w",
        "name": "شارژر فست شارژ انکر مدل 20 وات",
        "short_description": "آداپتور شارژ سریع PD با توان ۲۰ وات و پورت Type-C",
        "description": (
            "شارژر انکر ۲۰ وات با فناوری PowerIQ 3 و پشتیبانی از Power Delivery، گوشی‌های "
            "آیفون و اندروید را در کوتاه‌ترین زمان شارژ می‌کند."
        ),
        "price": "650000",
        "brand": "انکر",
        "category_slug": "mobile-accessories",
        "specifications": {"توان خروجی": "20 وات", "پورت": "USB-C", "استاندارد": "Power Delivery"},
        "initial_stock": 120,
    },
    {
        "sku": "BSS-CASE-A54",
        "slug": "baseus-case-a54",
        "name": "قاب محافظ گوشی بیسوس مناسب گلکسی A54",
        "short_description": "قاب سیلیکونی ضدضربه با پوشش دقیق دکمه‌ها و دوربین",
        "description": (
            "قاب محافظ بیسوس از جنس سیلیکون نرم، در برابر ضربه و خط‌وخش از گوشی محافظت می‌کند."
        ),
        "price": "210000",
        "brand": "بیسوس",
        "category_slug": "mobile-accessories",
        "specifications": {"جنس": "سیلیکون", "سازگاری": "Galaxy A54"},
        "initial_stock": 200,
    },
    {
        "sku": "ASU-VB15-I5",
        "slug": "asus-vivobook-15-i5",
        "name": "لپ‌تاپ ایسوس Vivobook 15 پردازنده Core i5",
        "short_description": "لپ‌تاپ همه‌کاره با پردازنده نسل ۱۲ اینتل و حافظه SSD",
        "description": (
            "ایسوس Vivobook 15 با پردازنده Core i5 نسل دوازدهم، ۸ گیگابایت رم و حافظه SSD "
            "۵۱۲ گیگابایتی، برای کارهای اداری و دانشجویی مناسب است."
        ),
        "price": "34900000",
        "brand": "ایسوس",
        "category_slug": "laptops",
        "specifications": {
            "پردازنده": "Intel Core i5-1235U",
            "رم": "8 گیگابایت",
            "حافظه": "512 گیگابایت SSD",
            "نمایشگر": "15.6 اینچ Full HD",
        },
        "initial_stock": 15,
        "is_featured": True,
    },
    {
        "sku": "LEN-IP3-I7",
        "slug": "lenovo-ideapad-3-i7",
        "name": "لپ‌تاپ لنوو IdeaPad 3 پردازنده Core i7",
        "short_description": "لپ‌تاپ قدرتمند با رم ۱۶ گیگابایت، مناسب چندوظیفگی سنگین",
        "description": (
            "لنوو IdeaPad 3 با پردازنده Core i7، ۱۶ گیگابایت رم و SSD یک ترابایتی، اجرای "
            "نرم‌افزارهای سنگین و چندوظیفگی را روان انجام می‌دهد."
        ),
        "price": "41200000",
        "brand": "لنوو",
        "category_slug": "laptops",
        "specifications": {
            "پردازنده": "Intel Core i7-1255U",
            "رم": "16 گیگابایت",
            "حافظه": "1 ترابایت SSD",
        },
        "initial_stock": 12,
    },
    {
        "sku": "APL-MBA-M2",
        "slug": "apple-macbook-air-m2",
        "name": "لپ‌تاپ اپل مک‌بوک ایر M2",
        "short_description": "مک‌بوک ایر فوق سبک با تراشه M2 و باتری تمام‌روز",
        "description": (
            "مک‌بوک ایر M2 با بدنه فوق‌سبک، تراشه اپل سیلیکون M2 و باتری تا ۱۸ ساعت، انتخابی "
            "برتر برای طراحان و برنامه‌نویسان است."
        ),
        "price": "68500000",
        "discount_price": "64900000",
        "brand": "اپل",
        "category_slug": "laptops",
        "specifications": {"تراشه": "Apple M2", "رم": "8 گیگابایت", "حافظه": "256 گیگابایت SSD"},
        "initial_stock": 10,
        "is_featured": True,
        "is_popular": True,
    },
    {
        "sku": "HP-PAV-R7",
        "slug": "hp-pavilion-ryzen7",
        "name": "لپ‌تاپ اچ‌پی Pavilion پردازنده Ryzen 7",
        "short_description": "لپ‌تاپ گرافیک‌محور مناسب طراحی و گیمینگ سبک",
        "description": (
            "اچ‌پی Pavilion با پردازنده AMD Ryzen 7 و کارت گرافیک مجزا، هم برای کارهای گرافیکی "
            "و هم بازی‌های نه‌چندان سنگین مناسب است."
        ),
        "price": "39700000",
        "brand": "اچ‌پی",
        "category_slug": "laptops",
        "specifications": {"پردازنده": "AMD Ryzen 7 5825U", "گرافیک": "AMD Radeon"},
        "initial_stock": 14,
    },
    {
        "sku": "WD-SSD-1TB",
        "slug": "wd-ssd-1tb",
        "name": "حافظه SSD اینترنال وسترن دیجیتال 1 ترابایت",
        "short_description": "حافظه SSD با رابط NVMe و سرعت خواندن بالا",
        "description": (
            "حافظه SSD وسترن دیجیتال با فناوری NVMe، سرعت انتقال داده بالا برای سیستم‌عامل و "
            "بازی‌ها فراهم می‌کند."
        ),
        "price": "2450000",
        "brand": "وسترن دیجیتال",
        "category_slug": "computer-parts",
        "specifications": {"ظرفیت": "1 ترابایت", "رابط": "NVMe M.2"},
        "initial_stock": 60,
    },
    {
        "sku": "COR-RAM16",
        "slug": "corsair-ram-16gb",
        "name": "رم دسکتاپ کورسیر Vengeance 16 گیگابایت DDR4",
        "short_description": "رم DDR4 با فرکانس بالا مناسب گیمینگ و ویرایش",
        "description": (
            "رم کورسیر Vengeance با طراحی خنک‌کننده آلومینیومی و فرکانس 3200 مگاهرتز، عملکرد "
            "پایدار در بار سنگین ارائه می‌دهد."
        ),
        "price": "1850000",
        "brand": "کورسیر",
        "category_slug": "computer-parts",
        "specifications": {"ظرفیت": "16 گیگابایت", "فرکانس": "3200 مگاهرتز", "نوع": "DDR4"},
        "initial_stock": 45,
    },
    {
        "sku": "ASU-RTX4060",
        "slug": "asus-rtx-4060",
        "name": "کارت گرافیک ایسوس مدل RTX 4060",
        "short_description": "کارت گرافیک نسل جدید انویدیا مناسب گیمینگ ۱۴۴۰p",
        "description": (
            "کارت گرافیک ایسوس RTX 4060 با پشتیبانی از DLSS 3 و رهگیری پرتو، تجربه‌ای روان در "
            "بازی‌های امروزی فراهم می‌کند."
        ),
        "price": "24900000",
        "brand": "ایسوس",
        "category_slug": "computer-parts",
        "specifications": {"حافظه گرافیکی": "8 گیگابایت GDDR6", "پشتیبانی": "DLSS 3, Ray Tracing"},
        "initial_stock": 9,
        "is_featured": True,
    },
    {
        "sku": "LOG-MX3",
        "slug": "logitech-mx-master-3",
        "name": "ماوس بی‌سیم لاجیتک MX Master 3",
        "short_description": "ماوس حرفه‌ای با اسکرول الکترومغناطیسی و اتصال چندگانه",
        "description": (
            "لاجیتک MX Master 3 با اسکرول MagSpeed و امکان اتصال هم‌زمان به سه دستگاه، برای "
            "کاربران حرفه‌ای طراحی شده است."
        ),
        "price": "3200000",
        "brand": "لاجیتک",
        "category_slug": "computer-accessories",
        "specifications": {"اتصال": "بلوتوث / گیرنده USB", "تعداد دکمه": "7 عدد"},
        "initial_stock": 35,
        "is_popular": True,
    },
    {
        "sku": "RAP-KB61",
        "slug": "rapoo-keyboard-v500",
        "name": "کیبورد مکانیکال رپو مدل V500",
        "short_description": "کیبورد مکانیکال با نورپردازی و سوییچ بلو",
        "description": (
            "کیبورد مکانیکال رپو V500 با سوییچ‌های بلو و نورپردازی رنگی، مناسب گیمینگ و تایپ "
            "حرفه‌ای است."
        ),
        "price": "1450000",
        "brand": "رپو",
        "category_slug": "computer-accessories",
        "specifications": {"نوع سوییچ": "بلو مکانیکال", "نورپردازی": "RGB"},
        "initial_stock": 40,
    },
    {
        "sku": "SNY-WH1000",
        "slug": "sony-wh-1000xm5",
        "name": "هدفون بی‌سیم سونی WH-1000XM5",
        "short_description": "هدفون فلگ‌شیپ با حذف نویز فعال پیشرفته",
        "description": (
            "سونی WH-1000XM5 با فناوری حذف نویز فعال پیشرفته و کیفیت صدای بالا، یکی از بهترین "
            "هدفون‌های بی‌سیم بازار است."
        ),
        "price": "14500000",
        "brand": "سونی",
        "category_slug": "headphones",
        "specifications": {"حذف نویز": "فعال (ANC)", "باتری": "تا 30 ساعت"},
        "initial_stock": 22,
        "is_featured": True,
    },
    {
        "sku": "APL-AIRP2",
        "slug": "apple-airpods-2",
        "name": "ایرپاد اپل نسل دوم",
        "short_description": "هندزفری بی‌سیم اپل با اتصال سریع به دستگاه‌های iOS",
        "description": (
            "ایرپاد نسل دوم اپل با تراشه H1 و اتصال آسان به اکوسیستم اپل، برای مکالمه و "
            "موسیقی روزمره مناسب است."
        ),
        "price": "6900000",
        "brand": "اپل",
        "category_slug": "headphones",
        "specifications": {"تراشه": "Apple H1", "کیس شارژ": "استاندارد"},
        "initial_stock": 50,
        "is_popular": True,
    },
    {
        "sku": "JBL-FLIP6",
        "slug": "jbl-flip-6",
        "name": "اسپیکر بلوتوثی جی‌بی‌ال Flip 6",
        "short_description": "اسپیکر قابل‌حمل ضدآب با صدای قدرتمند",
        "description": (
            "اسپیکر جی‌بی‌ال Flip 6 با استاندارد ضدآب IP67 و صدای قدرتمند، برای استفاده در "
            "سفر و فضای باز مناسب است."
        ),
        "price": "4200000",
        "brand": "جی‌بی‌ال",
        "category_slug": "speakers",
        "specifications": {"مقاومت": "IP67 ضدآب و گردوغبار", "باتری": "تا 12 ساعت"},
        "initial_stock": 38,
    },
    {
        "sku": "SGX-TV55Q",
        "slug": "samsung-tv-55-qled",
        "name": "تلویزیون سامسونگ 55 اینچ QLED",
        "short_description": "تلویزیون هوشمند QLED با کیفیت تصویر 4K",
        "description": (
            "تلویزیون QLED سامسونگ در سایز 55 اینچ با رزولوشن 4K و پنل هوشمند Tizen، تجربه "
            "تماشای سینمایی در خانه فراهم می‌کند."
        ),
        "price": "32500000",
        "discount_price": "29900000",
        "brand": "سامسونگ",
        "category_slug": "televisions",
        "specifications": {"سایز صفحه": "55 اینچ", "رزولوشن": "4K UHD", "پنل": "QLED"},
        "initial_stock": 8,
        "is_featured": True,
    },
    {
        "sku": "LG-TV43UHD",
        "slug": "lg-tv-43-uhd",
        "name": "تلویزیون ال‌جی 43 اینچ UHD",
        "short_description": "تلویزیون هوشمند مقرون‌به‌صرفه با کیفیت 4K",
        "description": (
            "تلویزیون ال‌جی 43 اینچ با رزولوشن 4K و سیستم‌عامل webOS، گزینه‌ای اقتصادی برای "
            "اتاق نشیمن یا خواب است."
        ),
        "price": "18700000",
        "brand": "ال‌جی",
        "category_slug": "televisions",
        "specifications": {"سایز صفحه": "43 اینچ", "رزولوشن": "4K UHD"},
        "initial_stock": 16,
    },
    {
        "sku": "PHI-VAC2100",
        "slug": "philips-vacuum-2100",
        "name": "جاروبرقی فیلیپس مدل 2100 وات",
        "short_description": "جاروبرقی خانگی با قدرت مکش بالا و فیلتر HEPA",
        "description": (
            "جاروبرقی فیلیپس با توان 2100 وات و فیلتر HEPA، گردوغبار و آلرژن‌ها را به‌طور "
            "مؤثر جمع‌آوری می‌کند."
        ),
        "price": "3650000",
        "brand": "فیلیپس",
        "category_slug": "small-appliances",
        "specifications": {"توان": "2100 وات", "نوع فیلتر": "HEPA"},
        "initial_stock": 28,
    },
    {
        "sku": "BSH-BLND600",
        "slug": "bosch-blender-600",
        "name": "مخلوط‌کن بوش مدل 600 وات",
        "short_description": "مخلوط‌کن خانگی با پارچ شیشه‌ای و چند سرعت",
        "description": (
            "مخلوط‌کن بوش با موتور 600 واتی و پارچ شیشه‌ای مقاوم، برای تهیه اسموتی و سس‌های "
            "خانگی مناسب است."
        ),
        "price": "2150000",
        "brand": "بوش",
        "category_slug": "small-appliances",
        "specifications": {"توان": "600 وات", "جنس پارچ": "شیشه"},
        "initial_stock": 33,
    },
    {
        "sku": "SNW-REF20",
        "slug": "snowa-fridge-20cf",
        "name": "یخچال فریزر اسنوا 20 فوت",
        "short_description": "یخچال فریزر دوقلو با سیستم نوفراست و مصرف انرژی پایین",
        "description": (
            "یخچال فریزر اسنوا با ظرفیت 20 فوت و سیستم نوفراست، برای خانواده‌های متوسط با "
            "مصرف انرژی بهینه طراحی شده است."
        ),
        "price": "45900000",
        "brand": "اسنوا",
        "category_slug": "refrigerators",
        "specifications": {"ظرفیت": "20 فوت", "سیستم سرمایش": "نوفراست", "رده انرژی": "A+"},
        "initial_stock": 6,
    },
    {
        "sku": "SNY-PS5",
        "slug": "sony-ps5",
        "name": "کنسول بازی سونی PlayStation 5",
        "short_description": "کنسول نسل نهم با SSD فوق‌سریع و گرافیک 4K",
        "description": (
            "پلی‌استیشن 5 با حافظه SSD فوق‌سریع، پشتیبانی از رزولوشن 4K و رهگیری پرتو، "
            "پرتقاضاترین کنسول بازی روز است."
        ),
        "price": "36500000",
        "brand": "سونی",
        "category_slug": "game-consoles",
        "specifications": {"حافظه": "825 گیگابایت SSD", "رزولوشن خروجی": "تا 4K"},
        "initial_stock": 11,
        "is_featured": True,
        "is_popular": True,
    },
    {
        "sku": "SNY-DS5",
        "slug": "sony-dualsense",
        "name": "دسته بازی سونی DualSense",
        "short_description": "دسته بی‌سیم پلی‌استیشن 5 با بازخورد لمسی پیشرفته",
        "description": (
            "دسته DualSense با موتورهای بازخورد لمسی و ماشه‌های تطبیقی، حس لمس واقعی‌تری به "
            "بازی‌های PS5 می‌بخشد."
        ),
        "price": "3400000",
        "brand": "سونی",
        "category_slug": "gaming-accessories",
        "specifications": {"اتصال": "بلوتوث / کابل USB-C", "باتری": "قابل شارژ"},
        "initial_stock": 24,
    },
]

SHIPPING_ADDRESS = ShippingAddress(
    recipient_name="زهرا احمدی",
    province="تهران",
    city="تهران",
    address_line="خیابان ولیعصر، نرسیده به میدان ونک، پلاک ۱۲۴، واحد ۳",
    postal_code="1991634581",
    phone_number="09121234567",
)

TICKET_SUBJECT = "مشکل در پرداخت سفارش"

_WALLET_DEPOSIT_AMOUNT = Decimal("3000000")
_WALLET_ADMIN_CREDIT_AMOUNT = Decimal("200000")
_WALLET_ADMIN_CREDIT_REASON = "جبران تأخیر در ارسال سفارش قبلی (هدیه پشتیبانی)"


async def seed_categories(session: AsyncSession) -> dict[str, uuid.UUID]:
    category_service = CategoryService(session)
    category_repo = CategoryRepository(session)
    slug_to_id: dict[str, uuid.UUID] = {}

    for top_index, top in enumerate(CATEGORY_TREE):
        top_category = await category_repo.get_by_slug(top["slug"])
        if top_category is None:
            top_category = await category_service.create(
                CategoryCreate(name=top["name"], slug=top["slug"], sort_order=top_index)
            )
        slug_to_id[top["slug"]] = top_category.id

        for child_index, child in enumerate(top["children"]):
            child_category = await category_repo.get_by_slug(child["slug"])
            if child_category is None:
                child_category = await category_service.create(
                    CategoryCreate(
                        name=child["name"],
                        slug=child["slug"],
                        parent_id=top_category.id,
                        sort_order=child_index,
                    )
                )
            slug_to_id[child["slug"]] = child_category.id

    await session.flush()
    return slug_to_id


async def seed_products(session: AsyncSession, category_ids: dict[str, uuid.UUID]) -> None:
    product_service = ProductService(session)
    product_repo = ProductRepository(session)

    for item in PRODUCTS:
        image = category_placeholder_image(item["category_slug"])
        existing = await product_repo.get_by_slug_or_sku(item["slug"], item["sku"])
        if existing is not None:
            if existing.images != [image]:
                existing.images = [image]
            continue

        await product_service.create(
            ProductCreate(
                sku=item["sku"],
                name=item["name"],
                slug=item["slug"],
                short_description=item["short_description"],
                description=item["description"],
                price=Decimal(item["price"]),
                discount_price=Decimal(item["discount_price"])
                if item.get("discount_price")
                else None,
                brand=item["brand"],
                category_id=category_ids[item["category_slug"]],
                images=[image],
                specifications=item["specifications"],
                is_featured=item.get("is_featured", False),
                is_popular=item.get("is_popular", False),
                initial_stock=item["initial_stock"],
            )
        )

    await session.flush()


async def seed_users(session: AsyncSession) -> tuple[User, User]:
    user_repo = UserRepository(session)

    admin = await user_repo.get_by_email(ADMIN_EMAIL)
    if admin is None:
        admin = User(
            email=ADMIN_EMAIL.lower(),
            username="admin",
            hashed_password=hash_password(ADMIN_PASSWORD),
            first_name="مدیر",
            last_name="فروشگاه",
            role=UserRole.admin,
            is_active=True,
            is_verified=True,
        )
        user_repo.add(admin)

    customer = await user_repo.get_by_email(CUSTOMER_EMAIL)
    if customer is None:
        customer = User(
            email=CUSTOMER_EMAIL.lower(),
            username="customer",
            hashed_password=hash_password(CUSTOMER_PASSWORD),
            first_name="زهرا",
            last_name="احمدی",
            role=UserRole.customer,
            is_active=True,
            is_verified=True,
        )
        user_repo.add(customer)

    await session.flush()
    return admin, customer


async def _checkout_items(
    order_service: OrderService,
    cart_service: CartService,
    product_repo: ProductRepository,
    customer_id: uuid.UUID,
    items: list[tuple[str, int]],
) -> Order:
    for slug, quantity in items:
        product = await product_repo.get_by_slug(slug)
        assert product is not None, f"seed product missing: {slug}"
        await cart_service.add_item(customer_id, product.id, quantity)
    order = await order_service.checkout(customer_id, SHIPPING_ADDRESS)

    # checkout() deletes the cart's CartItem rows and flushes, but the
    # Cart.items collection already loaded in this session's identity map
    # (from add_item()'s get_or_create() calls above) isn't automatically
    # refreshed by those out-of-band session.delete() calls — so the *next*
    # call to this helper would see this order's already-cleared items
    # instead of a genuinely empty cart. Expiring the collection forces the
    # next selectinload to re-read it from the database. This only matters
    # here because the whole seed script deliberately reuses one session
    # across several checkouts for the same user; a real request handler
    # gets a fresh session (and thus a fresh identity map) every time.
    cart = await cart_service.repo.get_or_create(customer_id)
    order_service.session.expire(cart, ["items"])
    return order


def _demo_payment(
    *,
    order: Order,
    user_id: uuid.UUID,
    status: PaymentStatus,
    verified: bool,
    gateway_status: str,
) -> Payment:
    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        gateway="zarinpal",
        authority=f"DEMO-{order.id.hex[:20]}",
        amount=order.total,
        status=status,
        raw_gateway_response={"demo_seed": True, "gateway_status": gateway_status},
    )
    if verified:
        payment.reference_id = f"REF-{order.id.hex[:12]}"
        payment.verified_at = datetime.now(UTC)
    return payment


async def seed_orders_payments_and_wallet_refund(
    session: AsyncSession, admin: User, customer: User
) -> None:
    order_repo = OrderRepository(session)
    _, existing_count = await order_repo.list_for_user(customer.id, offset=0, limit=1)
    if existing_count > 0:
        logger.info(
            "orders_already_seeded", user_id=str(customer.id), existing_orders=existing_count
        )
        return

    order_service = OrderService(session)
    cart_service = CartService(session)
    product_repo = ProductRepository(session)
    payment_repo = PaymentRepository(session)

    # Order A: full happy path, delivered and paid.
    order_a = await _checkout_items(
        order_service,
        cart_service,
        product_repo,
        customer.id,
        [("samsung-galaxy-a54", 1), ("jbl-flip-6", 1)],
    )
    await order_service.mark_paid(order_a.id)
    await order_service.admin_update_status(
        order_a.id, OrderStatus.processing, "سفارش بسته‌بندی و آماده ارسال شد.", admin.id
    )
    await order_service.admin_update_status(
        order_a.id, OrderStatus.shipped, "سفارش توسط پست پیشتاز ارسال شد.", admin.id
    )
    await order_service.admin_update_status(
        order_a.id, OrderStatus.completed, "سفارش با موفقیت به مشتری تحویل داده شد.", admin.id
    )
    payment_repo.add(
        _demo_payment(
            order=order_a,
            user_id=customer.id,
            status=PaymentStatus.verified,
            verified=True,
            gateway_status="OK",
        )
    )

    # Order B: checkout completed, still waiting on the payment gateway.
    order_b = await _checkout_items(
        order_service, cart_service, product_repo, customer.id, [("apple-airpods-2", 1)]
    )
    payment_repo.add(
        _demo_payment(
            order=order_b,
            user_id=customer.id,
            status=PaymentStatus.initiated,
            verified=False,
            gateway_status="PENDING",
        )
    )

    # Order C: payment failed at the gateway, order cancelled afterwards.
    order_c = await _checkout_items(
        order_service, cart_service, product_repo, customer.id, [("logitech-mx-master-3", 2)]
    )
    await order_service.mark_payment_failed(order_c.id)
    payment_repo.add(
        _demo_payment(
            order=order_c,
            user_id=customer.id,
            status=PaymentStatus.failed,
            verified=False,
            gateway_status="NOK",
        )
    )
    await order_service.admin_update_status(
        order_c.id, OrderStatus.cancelled, "سفارش به دلیل ناموفق بودن پرداخت لغو شد.", admin.id
    )

    # Order D: delivered, then returned and refunded to the customer's wallet.
    order_d = await _checkout_items(
        order_service, cart_service, product_repo, customer.id, [("sony-dualsense", 2)]
    )
    await order_service.mark_paid(order_d.id)
    await order_service.admin_update_status(
        order_d.id, OrderStatus.processing, "سفارش بسته‌بندی و آماده ارسال شد.", admin.id
    )
    await order_service.admin_update_status(
        order_d.id, OrderStatus.shipped, "سفارش توسط پست پیشتاز ارسال شد.", admin.id
    )
    await order_service.admin_update_status(
        order_d.id, OrderStatus.completed, "سفارش با موفقیت به مشتری تحویل داده شد.", admin.id
    )
    payment_repo.add(
        _demo_payment(
            order=order_d,
            user_id=customer.id,
            status=PaymentStatus.verified,
            verified=True,
            gateway_status="OK",
        )
    )
    await session.flush()
    await order_service.admin_update_status(
        order_d.id,
        OrderStatus.refunded,
        "کالا توسط مشتری مرجوع و مبلغ آن به کیف پول واریز شد.",
        admin.id,
    )

    wallet_service = WalletService(session)
    await wallet_service.refund_order(customer.id, order_d.total, order_d.id, actor_id=admin.id)

    await session.flush()


async def seed_wallet_extras(session: AsyncSession, admin: User, customer: User) -> None:
    wallet_service = WalletService(session)
    wallet = await wallet_service.get_or_create(customer.id)

    existing_deposit = await session.execute(
        select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id,
            WalletTransaction.type == WalletTransactionType.deposit,
        )
    )
    if existing_deposit.scalar_one_or_none() is None:
        await wallet_service.deposit(customer.id, _WALLET_DEPOSIT_AMOUNT)

    existing_credit = await session.execute(
        select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id,
            WalletTransaction.note == _WALLET_ADMIN_CREDIT_REASON,
        )
    )
    if existing_credit.scalar_one_or_none() is None:
        await wallet_service.admin_credit(
            customer.id, _WALLET_ADMIN_CREDIT_AMOUNT, _WALLET_ADMIN_CREDIT_REASON, actor_id=admin.id
        )

    await session.flush()


async def seed_ticket(session: AsyncSession, admin: User, customer: User) -> None:
    existing = await session.execute(
        select(Ticket).where(Ticket.user_id == customer.id, Ticket.subject == TICKET_SUBJECT)
    )
    if existing.scalar_one_or_none() is not None:
        logger.info("ticket_already_seeded", user_id=str(customer.id))
        return

    ticket_service = TicketService(session)
    ticket = await ticket_service.create(
        customer.id,
        TICKET_SUBJECT,
        "سلام، هنگام پرداخت سفارشم مبلغ از حساب بانکی‌ام کسر شد اما وضعیت سفارش همچنان "
        "«در انتظار پرداخت» نشان داده می‌شود. لطفاً بررسی کنید.",
        TicketPriority.high,
    )
    await session.flush()

    await ticket_service.add_support_reply(
        ticket.id,
        admin,
        "سلام، ضمن پوزش بابت این مشکل، بررسی کردیم؛ تراکنش شما توسط درگاه پرداخت تأیید نشده "
        "است، بنابراین مبلغی از حساب شما کسر نشده یا ظرف ۷۲ ساعت آینده به‌صورت خودکار بازگشت "
        "داده می‌شود.",
    )
    await ticket_service.add_customer_reply(
        ticket.id,
        customer,
        "متشکرم، بررسی کردم و همان‌طور که فرمودید مبلغ بازگشت داده شد. سفارش را دوباره ثبت "
        "می‌کنم.",
    )
    await ticket_service.add_support_reply(
        ticket.id,
        admin,
        "خیلی خوشحالیم که مشکل حل شد. در صورت بروز هرگونه سؤال دیگر، تیکت جدیدی ثبت کنید. "
        "این تیکت بسته می‌شود.",
    )
    await ticket_service.change_status(ticket.id, TicketStatus.closed)
    await session.flush()


async def _print_summary(session: AsyncSession) -> None:
    async def count(model: type) -> int:
        result = await session.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    counts = {
        "categories": await count(Category),
        "products": await count(Product),
        "users": await count(User),
        "orders": await count(Order),
        "payments": await count(Payment),
        "wallet_transactions": await count(WalletTransaction),
        "tickets": await count(Ticket),
        "ticket_messages": await count(TicketMessage),
    }

    print("\n=== خلاصه داده‌های نمایشی (Seed Summary) ===")
    for label, value in counts.items():
        print(f"  {label}: {value}")
    print("\nDemo admin login:")
    print(f"  email:    {ADMIN_EMAIL}")
    print(f"  password: {ADMIN_PASSWORD}")
    print("Demo customer login:")
    print(f"  email:    {CUSTOMER_EMAIL}")
    print(f"  password: {CUSTOMER_PASSWORD}")
    print("=============================================\n")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.debug)

    if settings.environment == "production":
        logger.warning("seed_running_in_production", environment=settings.environment)

    async with AsyncSessionFactory() as session:
        try:
            logger.info("seed_started")

            category_ids = await seed_categories(session)
            logger.info("seed_categories_done", count=len(category_ids))

            await seed_products(session, category_ids)
            logger.info("seed_products_done")

            admin, customer = await seed_users(session)
            logger.info("seed_users_done", admin_id=str(admin.id), customer_id=str(customer.id))

            await seed_orders_payments_and_wallet_refund(session, admin, customer)
            logger.info("seed_orders_done")

            await seed_wallet_extras(session, admin, customer)
            logger.info("seed_wallet_extras_done")

            await seed_ticket(session, admin, customer)
            logger.info("seed_ticket_done")

            await session.commit()
            logger.info("seed_completed")
        except Exception:
            await session.rollback()
            logger.exception("seed_failed")
            raise

        await _print_summary(session)


if __name__ == "__main__":
    asyncio.run(main())
