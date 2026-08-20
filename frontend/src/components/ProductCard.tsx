import { Link } from "react-router-dom";

import type { Product } from "@/api/types";
import { formatToman, toPersianDigits } from "@/lib/persian";
import { Badge } from "@/components/ui/Badge";

export function ProductCard({ product }: { product: Product }) {
  const hasDiscount = product.discount_price !== null;
  const outOfStock = product.available_stock <= 0;

  return (
    <Link
      to={`/products/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white transition-shadow hover:shadow-md dark:border-gray-800 dark:bg-gray-900"
    >
      <div className="relative flex aspect-square items-center justify-center bg-gray-50 dark:bg-gray-800">
        {product.images[0] ? (
          <img src={product.images[0]} alt={product.name} className="h-full w-full object-cover" />
        ) : (
          <span className="text-3xl font-bold text-gray-300 dark:text-gray-600">
            {product.name.charAt(0)}
          </span>
        )}
        {outOfStock && (
          <span className="absolute inset-x-0 top-0 bg-gray-900/80 py-1 text-center text-xs text-white">
            ناموجود
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-3">
        {product.brand && <span className="text-xs text-gray-400">{product.brand}</span>}
        <h3 className="line-clamp-2 min-h-[2.5rem] text-sm font-medium text-gray-900 dark:text-gray-100">
          {product.name}
        </h3>
        <div className="mt-auto flex items-center justify-between pt-1">
          <div className="flex flex-col">
            {hasDiscount && (
              <span className="text-xs text-gray-400 line-through">{formatToman(product.price)}</span>
            )}
            <span className="font-bold text-brand-700 dark:text-brand-500">
              {formatToman(product.discount_price ?? product.price)}
            </span>
          </div>
          {product.available_stock > 0 && product.available_stock <= 5 && (
            <Badge tone="warning">{`تنها ${toPersianDigits(product.available_stock)} عدد باقی مانده`}</Badge>
          )}
        </div>
      </div>
    </Link>
  );
}
