declare module "jalaali-js" {
  export interface JalaaliDate {
    jy: number;
    jm: number;
    jd: number;
  }

  export function toJalaali(date: Date): JalaaliDate;
  export function toJalaali(gy: number, gm: number, gd: number): JalaaliDate;
}
