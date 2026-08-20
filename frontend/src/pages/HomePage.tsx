import { Link } from "react-router-dom";

import { useCategoryTree } from "@/hooks/useCatalog";
import { useFeaturedProducts, usePopularProducts } from "@/hooks/useCatalog";
import { ProductCard } from "@/components/ProductCard";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";

export function HomePage() {
  const featured = useFeaturedProducts();
  const popular = usePopularProducts();
  const categories = useCategoryTree();

  return (
    <div className="flex flex-col gap-10">
      <section className="rounded-2xl bg-gradient-to-l from-brand-700 to-brand-600 px-6 py-10 text-white">
        <h1 className="text-2xl font-bold md:text-3xl">کالای دیجیتال با گارانتی اصالت</h1>
        <p className="mt-2 max-w-xl text-brand-100">
          موبایل، لپ‌تاپ، قطعات کامپیوتر و لوازم جانبی، با ارسال سریع و پرداخت امن.
        </p>
        <Link
          to="/products"
          className="mt-4 inline-block rounded-lg bg-white px-4 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50"
        >
          مشاهده همه محصولات
        </Link>
      </section>

      {categories.data && categories.data.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold">دسته‌بندی‌ها</h2>
          <div className="flex flex-wrap gap-2">
            {categories.data.map((category) => (
              <Link
                key={category.id}
                to={`/products?category_id=${category.id}`}
                className="rounded-full border border-gray-200 px-4 py-1.5 text-sm text-gray-700 hover:border-brand-500 hover:text-brand-700 dark:border-gray-700 dark:text-gray-200"
              >
                {category.name}
              </Link>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-bold">محصولات ویژه</h2>
        {featured.isLoading && <Spinner />}
        {featured.data && featured.data.length === 0 && (
          <EmptyState title="در حال حاضر محصول ویژه‌ای ثبت نشده است." />
        )}
        {featured.data && featured.data.length > 0 && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {featured.data.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-bold">پرطرفدارترین محصولات</h2>
        {popular.isLoading && <Spinner />}
        {popular.data && popular.data.length === 0 && (
          <EmptyState title="در حال حاضر محصول پرطرفداری ثبت نشده است." />
        )}
        {popular.data && popular.data.length > 0 && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {popular.data.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
