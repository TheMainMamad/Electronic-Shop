import { apiClient } from "@/lib/apiClient";
import type { Category, Page, Product } from "@/api/types";

export interface ProductListParams {
  page?: number;
  page_size?: number;
  category_id?: string;
  brand?: string;
  min_price?: string;
  max_price?: string;
  in_stock_only?: boolean;
  search?: string;
  sort_by?: "created_at" | "price" | "name";
  sort_desc?: boolean;
}

export async function fetchCategoryTree(): Promise<Category[]> {
  const { data } = await apiClient.get<Category[]>("/categories");
  return data;
}

export async function fetchProducts(params: ProductListParams): Promise<Page<Product>> {
  const { data } = await apiClient.get<Page<Product>>("/products", { params });
  return data;
}

export async function fetchFeaturedProducts(): Promise<Product[]> {
  const { data } = await apiClient.get<Product[]>("/products/featured");
  return data;
}

export async function fetchPopularProducts(): Promise<Product[]> {
  const { data } = await apiClient.get<Product[]>("/products/popular");
  return data;
}

export async function fetchProductBySlug(slug: string): Promise<Product> {
  const { data } = await apiClient.get<Product>(`/products/${slug}`);
  return data;
}

export function flattenCategories(categories: Category[]): Category[] {
  const result: Category[] = [];
  const walk = (nodes: Category[]) => {
    for (const node of nodes) {
      result.push(node);
      if (node.children.length > 0) walk(node.children);
    }
  };
  walk(categories);
  return result;
}
