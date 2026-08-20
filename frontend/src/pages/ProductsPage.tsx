import { useSearchParams } from "react-router-dom";

import { useCategoryTree, useProducts } from "@/hooks/useCatalog";
import { flattenCategories } from "@/api/catalog";
import { ProductCard } from "@/components/ProductCard";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Pagination } from "@/components/ui/Pagination";
import { Select } from "@/components/ui/Select";
import { getErrorMessage } from "@/lib/errors";

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const categories = useCategoryTree();
  const flatCategories = flattenCategories(categories.data ?? []);

  const page = Number(searchParams.get("page") ?? "1");
  const search = searchParams.get("search") ?? "";
  const categoryId = searchParams.get("category_id") ?? "";
  const sortBy = (searchParams.get("sort_by") as "created_at" | "price" | "name") ?? "created_at";
  const sortDesc = searchParams.get("sort_desc") !== "false";
  const inStockOnly = searchParams.get("in_stock_only") === "true";

  const products = useProducts({
    page,
    page_size: 12,
    search: search || undefined,
    category_id: categoryId || undefined,
    sort_by: sortBy,
    sort_desc: sortDesc,
    in_stock_only: inStockOnly || undefined,
  });

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    next.set("page", "1");
    setSearchParams(next);
  };

  return (
    <div className="flex flex-col gap-6 md:flex-row">
      <aside className="w-full shrink-0 md:w-56">
        <h2 className="mb-3 font-bold">فیلترها</h2>
        <div className="flex flex-col gap-3">
          <Select
            label="دسته‌بندی"
            value={categoryId}
            onChange={(event) => updateParam("category_id", event.target.value)}
          >
            <option value="">همه دسته‌بندی‌ها</option>
            {flatCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>

          <Select
            label="مرتب‌سازی"
            value={`${sortBy}:${sortDesc}`}
            onChange={(event) => {
              const [field, desc] = event.target.value.split(":");
              const next = new URLSearchParams(searchParams);
              next.set("sort_by", field);
              next.set("sort_desc", desc);
              next.set("page", "1");
              setSearchParams(next);
            }}
          >
            <option value="created_at:true">جدیدترین</option>
            <option value="price:false">ارزان‌ترین</option>
            <option value="price:true">گران‌ترین</option>
            <option value="name:false">نام (الف تا ی)</option>
          </Select>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(event) => updateParam("in_stock_only", event.target.checked ? "true" : "")}
            />
            فقط کالاهای موجود
          </label>
        </div>
      </aside>

      <div className="flex-1">
        {search && (
          <p className="mb-3 text-sm text-gray-500">
            نتایج جستجو برای: <span className="font-medium text-gray-800 dark:text-gray-200">«{search}»</span>
          </p>
        )}

        {products.isLoading && <Spinner />}
        {products.isError && <ErrorState message={getErrorMessage(products.error)} />}
        {products.data && products.data.items.length === 0 && (
          <EmptyState title="محصولی با این مشخصات پیدا نشد." description="فیلترهای دیگری را امتحان کنید." />
        )}
        {products.data && products.data.items.length > 0 && (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {products.data.items.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
            <Pagination
              page={products.data.page}
              totalPages={products.data.total_pages}
              onPageChange={(nextPage) => {
                const next = new URLSearchParams(searchParams);
                next.set("page", String(nextPage));
                setSearchParams(next);
              }}
            />
          </>
        )}
      </div>
    </div>
  );
}
