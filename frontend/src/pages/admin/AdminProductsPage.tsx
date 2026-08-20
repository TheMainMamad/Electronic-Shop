import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchProducts } from "@/api/catalog";
import { archiveProduct } from "@/api/admin";
import { formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { useToastStore } from "@/stores/toastStore";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function AdminProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const push = useToastStore((state) => state.push);
  const queryClient = useQueryClient();

  const products = useQuery({
    queryKey: ["admin", "products", page, searchParams.get("search")],
    queryFn: () =>
      fetchProducts({ page, page_size: 20, search: searchParams.get("search") || undefined }),
  });

  const archive = useMutation({
    mutationFn: (productId: string) => archiveProduct(productId),
    onSuccess: () => {
      push("محصول غیرفعال شد.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "products"] });
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-bold">محصولات</h1>
        <Link to="/admin/products/new">
          <Button>افزودن محصول</Button>
        </Link>
      </div>

      <form
        className="flex max-w-sm gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setSearchParams({ page: "1", search });
        }}
      >
        <Input placeholder="جستجوی محصول..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <Button type="submit" variant="secondary">
          جستجو
        </Button>
      </form>

      {products.isLoading && <Spinner />}
      {products.data && products.data.items.length === 0 && <EmptyState title="محصولی ثبت نشده است." />}
      {products.data && products.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                <tr>
                  <th className="px-3 py-2 text-right">نام</th>
                  <th className="px-3 py-2 text-right">SKU</th>
                  <th className="px-3 py-2 text-right">قیمت</th>
                  <th className="px-3 py-2 text-right">موجودی</th>
                  <th className="px-3 py-2 text-right">وضعیت</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {products.data.items.map((product) => (
                  <tr key={product.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="px-3 py-2">{product.name}</td>
                    <td className="ltr-inline px-3 py-2 text-xs text-gray-500">{product.sku}</td>
                    <td className="px-3 py-2">{formatToman(product.discount_price ?? product.price)}</td>
                    <td className="px-3 py-2">
                      {product.available_stock <= 0 ? (
                        <Badge tone="danger">ناموجود</Badge>
                      ) : product.available_stock <= 5 ? (
                        <Badge tone="warning">{product.available_stock}</Badge>
                      ) : (
                        product.available_stock
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <Badge tone={product.is_active ? "success" : "neutral"}>
                        {product.is_active ? "فعال" : "غیرفعال"}
                      </Badge>
                    </td>
                    <td className="flex gap-3 px-3 py-2">
                      <Link to={`/admin/products/${product.id}/edit`} className="text-brand-600 hover:underline">
                        ویرایش
                      </Link>
                      {product.is_active && (
                        <button
                          type="button"
                          className="text-red-600 hover:underline"
                          onClick={() => archive.mutate(product.id)}
                        >
                          غیرفعال‌سازی
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={products.data.page}
            totalPages={products.data.total_pages}
            onPageChange={(nextPage) => setSearchParams({ page: String(nextPage), search })}
          />
        </>
      )}
    </div>
  );
}
