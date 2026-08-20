import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchCategoryTree, flattenCategories } from "@/api/catalog";
import { createCategory, deleteCategory, moveCategory, updateCategory } from "@/api/admin";
import type { Category } from "@/api/types";
import { getErrorMessage } from "@/lib/errors";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .slice(0, 60) || `category-${Date.now()}`;
}

export function AdminCategoriesPage() {
  const queryClient = useQueryClient();
  const push = useToastStore((state) => state.push);
  const categories = useQuery({ queryKey: ["categories"], queryFn: fetchCategoryTree });
  const flatCategories = flattenCategories(categories.data ?? []);

  const [newName, setNewName] = useState("");
  const [newParentId, setNewParentId] = useState("");

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["categories"] });

  const create = useMutation({
    mutationFn: () =>
      createCategory({ name: newName, slug: slugify(newName), parent_id: newParentId || null }),
    onSuccess: () => {
      push("دسته‌بندی ایجاد شد.", "success");
      setNewName("");
      invalidate();
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      updateCategory(id, { is_active: isActive }),
    onSuccess: invalidate,
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const rename = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => updateCategory(id, { name }),
    onSuccess: invalidate,
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const move = useMutation({
    mutationFn: ({ id, parentId }: { id: string; parentId: string | null }) => moveCategory(id, parentId),
    onSuccess: invalidate,
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteCategory(id),
    onSuccess: () => {
      push("دسته‌بندی حذف شد.", "success");
      invalidate();
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const renderNode = (category: Category, depth: number) => (
    <div key={category.id} style={{ paddingRight: depth * 20 }} className="flex flex-col gap-1">
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 p-2 dark:border-gray-800">
        <input
          className="min-w-0 flex-1 rounded border border-transparent bg-transparent px-1 text-sm focus:border-gray-300 focus:outline-none dark:focus:border-gray-700"
          defaultValue={category.name}
          onBlur={(event) => {
            if (event.target.value !== category.name && event.target.value.trim()) {
              rename.mutate({ id: category.id, name: event.target.value.trim() });
            }
          }}
        />
        <Badge tone={category.is_active ? "success" : "neutral"}>
          {category.is_active ? "فعال" : "غیرفعال"}
        </Badge>
        <Select
          value={category.parent_id ?? ""}
          onChange={(event) => move.mutate({ id: category.id, parentId: event.target.value || null })}
          className="w-40"
        >
          <option value="">دسته اصلی (بدون والد)</option>
          {flatCategories
            .filter((c) => c.id !== category.id)
            .map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
        </Select>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => toggleActive.mutate({ id: category.id, isActive: !category.is_active })}
        >
          {category.is_active ? "غیرفعال‌سازی" : "فعال‌سازی"}
        </Button>
        <Button
          size="sm"
          variant="danger"
          onClick={() => {
            if (category.children.length > 0) {
              push("ابتدا زیردسته‌ها را حذف یا منتقل کنید.", "error");
              return;
            }
            remove.mutate(category.id);
          }}
        >
          حذف
        </Button>
      </div>
      {category.children.map((child) => renderNode(child, depth + 1))}
    </div>
  );

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">دسته‌بندی‌ها</h1>

      <Card>
        <h2 className="mb-3 font-bold">افزودن دسته‌بندی جدید</h2>
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate();
          }}
        >
          <Input label="نام دسته‌بندی" required value={newName} onChange={(e) => setNewName(e.target.value)} />
          <Select label="دسته والد (اختیاری)" value={newParentId} onChange={(e) => setNewParentId(e.target.value)}>
            <option value="">دسته اصلی</option>
            {flatCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
          <Button type="submit" loading={create.isPending}>
            افزودن
          </Button>
        </form>
      </Card>

      {categories.isLoading && <Spinner />}
      <div className="flex flex-col gap-2">
        {categories.data?.map((category) => renderNode(category, 0))}
      </div>
    </div>
  );
}
