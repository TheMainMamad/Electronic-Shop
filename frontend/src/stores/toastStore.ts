import { create } from "zustand";

export interface ToastMessage {
  id: number;
  text: string;
  tone: "success" | "error" | "info";
}

interface ToastState {
  toasts: ToastMessage[];
  push: (text: string, tone?: ToastMessage["tone"]) => void;
  dismiss: (id: number) => void;
}

let nextId = 1;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (text, tone = "info") => {
    const id = nextId++;
    set((state) => ({ toasts: [...state.toasts, { id, text, tone }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
