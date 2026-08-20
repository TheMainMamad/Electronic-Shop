import { Link, useNavigate } from "react-router-dom";

import { useCart, useClearCart, useRemoveCartItem, useUpdateCartItem } from "@/hooks/useCart";
import { useCurrentUser } from "@/hooks/useAuth";
import { formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { useToastStore } from "@/stores/toastStore";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";

export function CartPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const cart = useCart();
  const updateItem = useUpdateCartItem();
  const removeItem = useRemoveCartItem();
  const clearCart = useClearCart();
  const push = useToastStore((state) => state.push);
  const navigate = useNavigate();

  const onError = (err: unknown) => push(getErrorMessage(err), "error");

  if (userLoading) return <Spinner />;

  if (!user) {
    return (
      <EmptyState
        title="برای مشاهده سبد خرید وارد شوید."
        action={
          <Link to="/login" className="text-brand-600 hover:underline">
            ورود به حساب کاربری
          </Link>
        }
      />
    );
  }

  if (cart.isLoading) return <Spinner />;

  const items = cart.data?.items ?? [];

  if (items.length === 0) {
    return (
      <EmptyState
        title="سبد خرید شما خالی است."
        action={
          <Link to="/products" className="text-brand-600 hover:underline">
            مشاهده محصولات
          </Link>
        }
      />
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="flex flex-col gap-3 lg:col-span-2">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">سبد خرید</h1>
          <button
            type="button"
            className="text-sm text-red-600 hover:underline"
            onClick={() => clearCart.mutate(undefined, { onError })}
          >
            خالی‌کردن سبد
          </button>
        </div>

        {items.map((item) => (
          <div
            key={item.product_id}
            className="flex items-center gap-4 rounded-xl border border-gray-200 p-3 dark:border-gray-800"
          >
            <Link to={`/products/${item.slug}`} className="flex-1 font-medium hover:text-brand-600">
              {item.name}
            </Link>
            <span className="text-sm text-gray-500">{formatToman(item.unit_price)}</span>
            <div className="flex items-center rounded-lg border border-gray-300 dark:border-gray-700">
              <button
                type="button"
                className="px-2.5 py-1 text-lg"
                onClick={() =>
                  item.quantity > 1
                    ? updateItem.mutate(
                        { productId: item.product_id, quantity: item.quantity - 1 },
                        { onError },
                      )
                    : removeItem.mutate(item.product_id, { onError })
                }
              >
                −
              </button>
              <span className="w-8 text-center text-sm">{item.quantity}</span>
              <button
                type="button"
                className="px-2.5 py-1 text-lg disabled:opacity-40"
                disabled={item.quantity >= item.available_stock}
                onClick={() =>
                  updateItem.mutate(
                    { productId: item.product_id, quantity: item.quantity + 1 },
                    { onError },
                  )
                }
              >
                +
              </button>
            </div>
            <span className="w-28 text-left font-bold">{formatToman(item.subtotal)}</span>
            <button
              type="button"
              className="text-sm text-gray-400 hover:text-red-600"
              onClick={() => removeItem.mutate(item.product_id, { onError })}
            >
              حذف
            </button>
          </div>
        ))}
      </div>

      <div className="h-fit rounded-xl border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-bold">خلاصه سفارش</h2>
        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300">
          <span>جمع جزء</span>
          <span>{formatToman(cart.data?.subtotal ?? "0")}</span>
        </div>
        <div className="mt-2 flex justify-between border-t border-gray-100 pt-2 font-bold dark:border-gray-800">
          <span>مبلغ قابل پرداخت</span>
          <span>{formatToman(cart.data?.total ?? "0")}</span>
        </div>
        <Button className="mt-4 w-full" onClick={() => navigate("/checkout")}>
          ادامه فرایند خرید
        </Button>
      </div>
    </div>
  );
}
