import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useProduct } from "@/hooks/useCatalog";
import { useAddToCart } from "@/hooks/useCart";
import { useCurrentUser } from "@/hooks/useAuth";
import { formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { useToastStore } from "@/stores/toastStore";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { Badge } from "@/components/ui/Badge";

export function ProductDetailPage() {
  const { slug = "" } = useParams();
  const { data: product, isLoading, isError, error } = useProduct(slug);
  const { data: user } = useCurrentUser();
  const addToCart = useAddToCart();
  const push = useToastStore((state) => state.push);
  const navigate = useNavigate();
  const [quantity, setQuantity] = useState(1);

  if (isLoading) return <Spinner />;
  if (isError || !product) return <ErrorState message={getErrorMessage(error, "محصول موردنظر پیدا نشد.")} />;

  const outOfStock = product.available_stock <= 0;

  const handleAddToCart = () => {
    if (!user) {
      navigate("/login");
      return;
    }
    addToCart.mutate(
      { productId: product.id, quantity },
      {
        onSuccess: () => push("محصول به سبد خرید اضافه شد.", "success"),
        onError: (err) => push(getErrorMessage(err), "error"),
      },
    );
  };

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <div className="flex aspect-square items-center justify-center rounded-xl bg-gray-50 dark:bg-gray-900">
        {product.images[0] ? (
          <img src={product.images[0]} alt={product.name} className="h-full w-full rounded-xl object-cover" />
        ) : (
          <span className="text-6xl font-bold text-gray-300 dark:text-gray-700">{product.name.charAt(0)}</span>
        )}
      </div>

      <div className="flex flex-col gap-4">
        <div>
          {product.brand && <span className="text-sm text-gray-400">{product.brand}</span>}
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{product.name}</h1>
          <span className="ltr-inline text-xs text-gray-400">SKU: {product.sku}</span>
        </div>

        <div className="flex items-center gap-3">
          {product.discount_price && (
            <span className="text-gray-400 line-through">{formatToman(product.price)}</span>
          )}
          <span className="text-2xl font-bold text-brand-700 dark:text-brand-500">
            {formatToman(product.discount_price ?? product.price)}
          </span>
        </div>

        <div>
          {outOfStock ? (
            <Badge tone="danger">ناموجود</Badge>
          ) : (
            <Badge tone="success">موجود در انبار</Badge>
          )}
        </div>

        {product.short_description && (
          <p className="text-sm text-gray-600 dark:text-gray-300">{product.short_description}</p>
        )}

        {!outOfStock && (
          <div className="flex items-center gap-3">
            <div className="flex items-center rounded-lg border border-gray-300 dark:border-gray-700">
              <button
                type="button"
                className="px-3 py-2 text-lg"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              >
                −
              </button>
              <span className="w-10 text-center">{quantity}</span>
              <button
                type="button"
                className="px-3 py-2 text-lg"
                onClick={() => setQuantity((q) => Math.min(product.available_stock, q + 1))}
              >
                +
              </button>
            </div>
            <Button onClick={handleAddToCart} loading={addToCart.isPending}>
              افزودن به سبد خرید
            </Button>
          </div>
        )}

        {!user && (
          <p className="text-sm text-gray-500">
            برای خرید ابتدا{" "}
            <Link to="/login" className="text-brand-600 hover:underline">
              وارد حساب کاربری خود شوید
            </Link>
            .
          </p>
        )}

        {Object.keys(product.specifications).length > 0 && (
          <div>
            <h2 className="mb-2 font-bold">مشخصات فنی</h2>
            <table className="w-full border-collapse overflow-hidden rounded-lg text-sm">
              <tbody>
                {Object.entries(product.specifications).map(([key, value]) => (
                  <tr key={key} className="border-b border-gray-100 last:border-0 dark:border-gray-800">
                    <td className="w-1/2 bg-gray-50 px-3 py-2 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                      {key}
                    </td>
                    <td className="px-3 py-2">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {product.description && (
          <div>
            <h2 className="mb-2 font-bold">توضیحات</h2>
            <p className="whitespace-pre-line text-sm text-gray-600 dark:text-gray-300">
              {product.description}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
