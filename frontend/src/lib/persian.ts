import { toJalaali } from "jalaali-js";

const PERSIAN_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

const JALALI_MONTHS = [
  "فروردین",
  "اردیبهشت",
  "خرداد",
  "تیر",
  "مرداد",
  "شهریور",
  "مهر",
  "آبان",
  "آذر",
  "دی",
  "بهمن",
  "اسفند",
];

export function toPersianDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (digit) => PERSIAN_DIGITS[Number(digit)]);
}

export function formatToman(amount: string | number): string {
  const numeric = typeof amount === "string" ? amount : String(amount);
  const withSeparators = numeric.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${toPersianDigits(withSeparators)} تومان`;
}

export function formatNumber(value: number): string {
  return toPersianDigits(value.toLocaleString("en-US"));
}

export function formatJalaliDate(isoDate: string): string {
  const date = new Date(isoDate);
  const { jy, jm, jd } = toJalaali(date);
  return `${toPersianDigits(jd)} ${JALALI_MONTHS[jm - 1]} ${toPersianDigits(jy)}`;
}

export function formatJalaliDateTime(isoDate: string): string {
  const date = new Date(isoDate);
  const time = date.toLocaleTimeString("fa-IR", { hour: "2-digit", minute: "2-digit" });
  return `${formatJalaliDate(isoDate)} - ${toPersianDigits(time)}`;
}
