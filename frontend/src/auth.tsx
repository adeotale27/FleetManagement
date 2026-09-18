import { createContext, useContext } from "react";
import type { User } from "./types";

export const AuthContext = createContext<{
  user: User | null;
  setUser: (u: User | null) => void;
  logout: () => void;
}>({ user: null, setUser: () => undefined, logout: () => undefined });

export function useAuth() {
  return useContext(AuthContext);
}

export function can(permissions: string[] | undefined, perm: string) {
  return Boolean(permissions?.includes(perm) || permissions?.includes("*") || permissions?.some((p) => p.endsWith(":*") && perm.startsWith(p.slice(0, -1))));
}
