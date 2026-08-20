import { useQuery } from "@tanstack/react-query";

import { fetchCategoryTree, fetchFeaturedProducts, fetchPopularProducts, fetchProductBySlug, fetchProducts } from "@/api/catalog";
import type { ProductListParams } from "@/api/catalog";

export function useCategoryTree() {
  return useQuery({ queryKey: ["categories"], queryFn: fetchCategoryTree, staleTime: 5 * 60_000 });
}

export function useFeaturedProducts() {
  return useQuery({ queryKey: ["products", "featured"], queryFn: fetchFeaturedProducts, staleTime: 60_000 });
}

export function usePopularProducts() {
  return useQuery({ queryKey: ["products", "popular"], queryFn: fetchPopularProducts, staleTime: 60_000 });
}

export function useProducts(params: ProductListParams) {
  return useQuery({ queryKey: ["products", "list", params], queryFn: () => fetchProducts(params) });
}

export function useProduct(slug: string) {
  return useQuery({ queryKey: ["products", "detail", slug], queryFn: () => fetchProductBySlug(slug) });
}
