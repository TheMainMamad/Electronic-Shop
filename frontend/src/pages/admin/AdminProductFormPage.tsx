import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchProductBySlug, fetchProducts, flattenCategories } from "@/api/catalog";
import { createProduct, updateProduct, uploadProductImage } from "@/api/admin";
import type { AdminProductPayload } from "@/api/admin";
import { useCategoryTree } from "@/hooks/useCatalog";
import { getErrorMessage } from "@/lib/errors";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";

interface SpecRow {
  key: string;
  value: string;
}

const EMPTY_FORM: AdminProductPayload = {
  sku: "",
  name: "",
  slug: "",
  short_description: "",
  description: "",
  price: "",
  discount_price: "",
  brand: "",
  category_id: "",
  images: [],
  specifications: {},
  is_active: true,
  is_featured: false,
  is_popular: false,
  initial_stock: 0,
};

export function AdminProductFormPage() {
  const { id } = useParams();
  const isEditMode = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const push = useToastStore((state) => state.push);
  const categories = useCategoryTree();
  const flatCategories = flattenCategories(categories.data ?? []);

  const [form, setForm] = useState<AdminProductPayload>(EMPTY_FORM);
  const [specs, setSpecs] = useState<SpecRow[]>([{ key: "", value: "" }]);
  const [error, setError] = useState("");

  // Products are keyed by slug for lookups elsewhere in the app; the admin
  // list only gives us the id, so resolve the product for editing via a
  // filtered search (small dataset, acceptable for admin tooling).
  const existingProduct = useQuery({
    queryKey: ["admin", "products", "byId", id],
    queryFn: async () => {
      const page = await fetchProducts({ page: 1, page_size: 100 });
      const match = page.items.find((item) => item.id === id);
      if (!match) throw new Error("محصول پیدا نشد.");
      return fetchProductBySlug(match.slug);
    },
    enabled: isEditMode,
  });

  useEffect(() => {
    if (existingProduct.data) {
      const product = existingProduct.data;
      setForm({
        sku: product.sku,
        name: product.name,
        slug: product.slug,
        short_description: product.short_description,
        description: product.description,
        price: product.price,
        discount_price: product.discount_price ?? "",
        brand: product.brand,
        category_id: product.category_id,
        images: product.images,
        specifications: product.specifications,
        is_active: product.is_active,
        is_featured: product.is_featured,
        is_popular: product.is_popular,
      });
      const rows = Object.entries(product.specifications).map(([key, value]) => ({ key, value }));
      setSpecs(rows.length > 0 ? rows : [{ key: "", value: "" }]);
    }
  }, [existingProduct.data]);

  const submit = useMutation({
    mutationFn: () => {
      const specifications = Object.fromEntries(
        specs.filter((row) => row.key.trim()).map((row) => [row.key.trim(), row.value]),
      );
      const payload = { ...form, specifications, discount_price: form.discount_price || null };
      return isEditMode ? updateProduct(id!, payload) : createProduct(payload);
    },
    onSuccess: () => {
      push(isEditMode ? "محصول به‌روزرسانی شد." : "محصول ایجاد شد.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "products"] });
      navigate("/admin/products");
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const uploadImage = useMutation({
    mutationFn: (file: File) => uploadProductImage(file),
    onSuccess: (result) => setForm((prev) => ({ ...prev, images: [...(prev.images ?? []), result.url] })),
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  if (isEditMode && existingProduct.isLoading) return <Spinner />;

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-4 text-xl font-bold">{isEditMode ? "ویرایش محصول" : "افزودن محصول"}</h1>
      <Card>
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            setError("");
            submit.mutate();
          }}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="نام محصول" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input
              label="نامک (Slug)"
              required
              ltr
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
            />
            <Input label="SKU" required ltr value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
            <Input label="برند" value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
            <Select
              label="دسته‌بندی"
              required
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            >
              <option value="">انتخاب کنید</option>
              {flatCategories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Select>
            <Input
              label="قیمت (تومان)"
              type="number"
              required
              min={1}
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
            />
            <Input
              label="قیمت با تخفیف (اختیاری)"
              type="number"
              min={0}
              value={form.discount_price ?? ""}
              onChange={(e) => setForm({ ...form, discount_price: e.target.value })}
            />
            {!isEditMode && (
              <Input
                label="موجودی اولیه"
                type="number"
                min={0}
                value={form.initial_stock}
                onChange={(e) => setForm({ ...form, initial_stock: Number(e.target.value) })}
              />
            )}
          </div>

          <Input
            label="توضیح کوتاه"
            value={form.short_description}
            onChange={(e) => setForm({ ...form, short_description: e.target.value })}
          />
          <Textarea
            label="توضیحات کامل"
            rows={4}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />

          <div>
            <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">مشخصات فنی</span>
            <div className="flex flex-col gap-2">
              {specs.map((row, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder="عنوان (مثلاً حافظه رم)"
                    value={row.key}
                    onChange={(e) => {
                      const next = [...specs];
                      next[index] = { ...next[index], key: e.target.value };
                      setSpecs(next);
                    }}
                  />
                  <Input
                    placeholder="مقدار (مثلاً 16GB)"
                    value={row.value}
                    onChange={(e) => {
                      const next = [...specs];
                      next[index] = { ...next[index], value: e.target.value };
                      setSpecs(next);
                    }}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setSpecs(specs.filter((_, i) => i !== index))}
                  >
                    حذف
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="w-fit"
                onClick={() => setSpecs([...specs, { key: "", value: "" }])}
              >
                افزودن مشخصه
              </Button>
            </div>
          </div>

          <div>
            <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">تصاویر</span>
            <div className="flex flex-wrap gap-2">
              {(form.images ?? []).map((url) => (
                <img key={url} src={url} alt="" className="h-16 w-16 rounded-lg object-cover" />
              ))}
            </div>
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="mt-2 text-sm"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) uploadImage.mutate(file);
              }}
            />
          </div>

          <div className="flex flex-wrap gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              />
              فعال
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_featured}
                onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
              />
              محصول ویژه
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_popular}
                onChange={(e) => setForm({ ...form, is_popular: e.target.checked })}
              />
              پرطرفدار
            </label>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" loading={submit.isPending} className="w-fit">
            {isEditMode ? "ذخیره تغییرات" : "ایجاد محصول"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
