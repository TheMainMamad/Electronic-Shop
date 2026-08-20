import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { useCart } from "@/hooks/useCart";
import { checkout } from "@/api/orders";
import { initPayment } from "@/api/payments";
import type { ShippingAddress } from "@/api/types";
import { formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";

const EMPTY_ADDRESS: ShippingAddress = {
  recipient_name: "",
  province: "",
  city: "",
  address_line: "",
  postal_code: "",
  phone_number: "",
};

export function CheckoutPage() {
  const cart = useCart();
  const navigate = useNavigate();
  const [address, setAddress] = useState<ShippingAddress>(EMPTY_ADDRESS);
  const [error, setError] = useState("");

  const submit = useMutation({
    mutationFn: async () => {
      const order = await checkout(address);
      const payment = await initPayment(order.id);
      return payment;
    },
    onSuccess: (payment) => {
      window.location.href = payment.payment_url;
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const update = (field: keyof ShippingAddress) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setAddress((prev) => ({ ...prev, [field]: event.target.value }));

  if (cart.isLoading) return <Spinner />;
  if (!cart.data || cart.data.items.length === 0) {
    return <EmptyState title="سبد خرید شما خالی است." />;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <h1 className="mb-4 text-xl font-bold">تسویه‌حساب</h1>
        <Card>
          <h2 className="mb-3 font-bold">آدرس ارسال</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="نام گیرنده" required value={address.recipient_name} onChange={update("recipient_name")} />
            <Input label="شماره تماس" required ltr value={address.phone_number} onChange={update("phone_number")} />
            <Input label="استان" required value={address.province} onChange={update("province")} />
            <Input label="شهر" required value={address.city} onChange={update("city")} />
            <Input
              label="آدرس کامل"
              required
              className="sm:col-span-2"
              value={address.address_line}
              onChange={update("address_line")}
            />
            <Input label="کد پستی" required ltr value={address.postal_code} onChange={update("postal_code")} />
          </div>
        </Card>
      </div>

      <div className="h-fit rounded-xl border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-bold">خلاصه سفارش</h2>
        {cart.data.items.map((item) => (
          <div key={item.product_id} className="flex justify-between py-1 text-sm">
            <span>
              {item.name} × {item.quantity}
            </span>
            <span>{formatToman(item.subtotal)}</span>
          </div>
        ))}
        <div className="mt-2 flex justify-between border-t border-gray-100 pt-2 font-bold dark:border-gray-800">
          <span>مبلغ قابل پرداخت</span>
          <span>{formatToman(cart.data.total)}</span>
        </div>

        {error && <ErrorState message={error} />}

        <Button
          className="mt-4 w-full"
          loading={submit.isPending}
          onClick={() => {
            setError("");
            submit.mutate();
          }}
        >
          پرداخت و ثبت سفارش
        </Button>
        <button
          type="button"
          className="mt-2 w-full text-center text-xs text-gray-400 hover:underline"
          onClick={() => navigate("/cart")}
        >
          بازگشت به سبد خرید
        </button>
      </div>
    </div>
  );
}
