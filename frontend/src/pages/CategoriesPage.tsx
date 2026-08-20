import { Link } from "react-router-dom";

import type { Category } from "@/api/types";
import { useCategoryTree } from "@/hooks/useCatalog";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card } from "@/components/ui/Card";

function CategoryNode({ category }: { category: Category }) {
  return (
    <li>
      <Link to={`/products?category_id=${category.id}`} className="font-medium text-gray-800 hover:text-brand-600 dark:text-gray-100">
        {category.name}
      </Link>
      {category.children.length > 0 && (
        <ul className="mt-2 mr-4 flex flex-col gap-2 border-r border-gray-200 pr-4 dark:border-gray-800">
          {category.children.map((child) => (
            <CategoryNode key={child.id} category={child} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function CategoriesPage() {
  const { data, isLoading } = useCategoryTree();

  if (isLoading) return <Spinner />;
  if (!data || data.length === 0) {
    return <EmptyState title="دسته‌بندی‌ای ثبت نشده است." />;
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">دسته‌بندی‌ها</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((category) => (
          <Card key={category.id}>
            <ul className="flex flex-col gap-2">
              <CategoryNode category={category} />
            </ul>
          </Card>
        ))}
      </div>
    </div>
  );
}
