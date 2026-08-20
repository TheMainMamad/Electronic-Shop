import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { addCartItem, clearCart, fetchCart, removeCartItem, updateCartItem } from "@/api/cart";
import { useCurrentUser } from "@/hooks/useAuth";

export const CART_QUERY_KEY = ["cart"];

export function useCart() {
  const { data: user } = useCurrentUser();
  return useQuery({
    queryKey: CART_QUERY_KEY,
    queryFn: fetchCart,
    enabled: Boolean(user),
    staleTime: 10_000,
  });
}

export function useAddToCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      addCartItem(productId, quantity),
    onSuccess: (data) => queryClient.setQueryData(CART_QUERY_KEY, data),
  });
}

export function useUpdateCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      updateCartItem(productId, quantity),
    onSuccess: (data) => queryClient.setQueryData(CART_QUERY_KEY, data),
  });
}

export function useRemoveCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (productId: string) => removeCartItem(productId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CART_QUERY_KEY }),
  });
}

export function useClearCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: clearCart,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CART_QUERY_KEY }),
  });
}
